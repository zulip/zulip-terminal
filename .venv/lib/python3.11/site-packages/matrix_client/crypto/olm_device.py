import logging

import olm
from canonicaljson import encode_canonical_json

from matrix_client.checks import check_user_id
from matrix_client.crypto.one_time_keys import OneTimeKeysManager

logger = logging.getLogger(__name__)


class OlmDevice(object):
    """Manages the Olm cryptographic functions.

    Has a unique Olm account which holds identity keys.

    Args:
        api (MatrixHttpApi): The api object used to make requests.
        user_id (str): Matrix user ID. Must match the one used when logging in.
        device_id (str): Must match the one used when logging in.
        signed_keys_proportion (float): Optional. The proportion of signed one-time keys
            we should maintain on the HS compared to unsigned keys. The maximum value of
            ``1`` means only signed keys will be uploaded, while the minimum value of
            ``0`` means only unsigned keys. The actual amount of keys is determined at
            runtime from the given proportion and the maximum number of one-time keys
            we can physically hold.
        keys_threshold (float): Optional. Threshold below which a one-time key
            replenishment is triggered. Must be between ``0`` and ``1``. For example,
            ``0.1`` means that new one-time keys will be uploaded when there is less than
            10% of the maximum number of one-time keys on the server.
    """

    _olm_algorithm = 'm.olm.v1.curve25519-aes-sha2'
    _megolm_algorithm = 'm.megolm.v1.aes-sha2'
    _algorithms = [_olm_algorithm, _megolm_algorithm]

    def __init__(self,
                 api,
                 user_id,
                 device_id,
                 signed_keys_proportion=1,
                 keys_threshold=0.1):
        if not 0 <= signed_keys_proportion <= 1:
            raise ValueError('signed_keys_proportion must be between 0 and 1.')
        if not 0 <= keys_threshold <= 1:
            raise ValueError('keys_threshold must be between 0 and 1.')
        self.api = api
        check_user_id(user_id)
        self.user_id = user_id
        self.device_id = device_id
        self.olm_account = olm.Account()
        logger.info('Initialised Olm Device.')
        self.identity_keys = self.olm_account.identity_keys
        # Try to maintain half the number of one-time keys libolm can hold uploaded
        # on the HS. This is because some keys will be claimed by peers but not
        # used instantly, and we want them to stay in libolm, until the limit is reached
        # and it starts discarding keys, starting by the oldest.
        target_keys_number = self.olm_account.max_one_time_keys // 2
        self.one_time_keys_manager = OneTimeKeysManager(target_keys_number,
                                                        signed_keys_proportion,
                                                        keys_threshold)

    def upload_identity_keys(self):
        """Uploads this device's identity keys to HS.

        This device must be the one used when logging in.
        """
        device_keys = {
            'user_id': self.user_id,
            'device_id': self.device_id,
            'algorithms': self._algorithms,
            'keys': {'{}:{}'.format(alg, self.device_id): key
                     for alg, key in self.identity_keys.items()}
        }
        self.sign_json(device_keys)
        ret = self.api.upload_keys(device_keys=device_keys)
        self.one_time_keys_manager.server_counts = ret['one_time_key_counts']
        logger.info('Uploaded identity keys.')

    def upload_one_time_keys(self, force_update=False):
        """Uploads new one-time keys to the HS, if needed.

        Args:
            force_update (bool): Fetch the number of one-time keys currently on the HS
                before uploading, even if we already know one. In most cases this should
                not be necessary, as we get this value from sync responses.

        Returns:
            A dict containg the number of new keys that were uploaded for each key type
                (signed_curve25519 or curve25519). The format is
                ``<key_type>: <uploaded_number>``. If no keys of a given type have been
                uploaded, the corresponding key will not be present. Consequently, an
                empty dict indicates that no keys were uploaded.
        """
        if force_update or not self.one_time_keys_manager.server_counts:
            counts = self.api.upload_keys()['one_time_key_counts']
            self.one_time_keys_manager.server_counts = counts

        signed_keys_to_upload = self.one_time_keys_manager.signed_curve25519_to_upload
        unsigned_keys_to_upload = self.one_time_keys_manager.curve25519_to_upload

        self.olm_account.generate_one_time_keys(signed_keys_to_upload +
                                                unsigned_keys_to_upload)

        one_time_keys = {}
        keys = self.olm_account.one_time_keys['curve25519']
        for i, key_id in enumerate(keys):
            if i < signed_keys_to_upload:
                key = self.sign_json({'key': keys[key_id]})
                key_type = 'signed_curve25519'
            else:
                key = keys[key_id]
                key_type = 'curve25519'
            one_time_keys['{}:{}'.format(key_type, key_id)] = key

        ret = self.api.upload_keys(one_time_keys=one_time_keys)
        self.one_time_keys_manager.server_counts = ret['one_time_key_counts']
        self.olm_account.mark_keys_as_published()

        keys_uploaded = {}
        if unsigned_keys_to_upload:
            keys_uploaded['curve25519'] = unsigned_keys_to_upload
        if signed_keys_to_upload:
            keys_uploaded['signed_curve25519'] = signed_keys_to_upload
        logger.info('Uploaded new one-time keys: %s.', keys_uploaded)
        return keys_uploaded

    def update_one_time_key_counts(self, counts):
        """Update data on one-time keys count and upload new ones if necessary.

        Args:
            counts (dict): Counts of keys currently on the HS for each key type.
        """
        self.one_time_keys_manager.server_counts = counts
        if self.one_time_keys_manager.should_upload():
            logger.info('Uploading new one-time keys.')
            self.upload_one_time_keys()

    def sign_json(self, json):
        """Signs a JSON object.

        NOTE: The object is modified in-place and the return value can be ignored.

        As specified, this is done by encoding the JSON object without ``signatures`` or
        keys grouped as ``unsigned``, using canonical encoding.

        Args:
            json (dict): The JSON object to sign.

        Returns:
            The same JSON object, with a ``signatures`` key added. It is formatted as
            ``"signatures": ed25519:<device_id>: <base64_signature>``.
        """
        signatures = json.pop('signatures', {})
        unsigned = json.pop('unsigned', None)

        signature_base64 = self.olm_account.sign(encode_canonical_json(json))

        key_id = 'ed25519:{}'.format(self.device_id)
        signatures.setdefault(self.user_id, {})[key_id] = signature_base64

        json['signatures'] = signatures
        if unsigned:
            json['unsigned'] = unsigned

        return json

    def verify_json(self, json, user_key, user_id, device_id):
        """Verifies a signed key object's signature.

        The object must have a 'signatures' key associated with an object of the form
        `user_id: {key_id: signature}`.

        Args:
            json (dict): The JSON object to verify.
            user_key (str): The public ed25519 key which was used to sign the object.
            user_id (str): The user who owns the device.
            device_id (str): The device who owns the key.

        Returns:
            True if the verification was successful, False if not.
        """
        try:
            signatures = json.pop('signatures')
        except KeyError:
            return False

        key_id = 'ed25519:{}'.format(device_id)
        try:
            signature_base64 = signatures[user_id][key_id]
        except KeyError:
            json['signatures'] = signatures
            return False

        unsigned = json.pop('unsigned', None)

        try:
            olm.ed25519_verify(user_key, encode_canonical_json(json), signature_base64)
            success = True
        except olm.utility.OlmVerifyError:
            success = False

        json['signatures'] = signatures
        if unsigned:
            json['unsigned'] = unsigned

        return success
