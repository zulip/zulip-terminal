class OneTimeKeysManager(object):
    """Handles one-time keys accounting for an OlmDevice."""

    def __init__(self, target_keys_number, signed_keys_proportion, keys_threshold):
        self.target_counts = {
            'signed_curve25519': int(round(signed_keys_proportion * target_keys_number)),
            'curve25519': int(round((1 - signed_keys_proportion) * target_keys_number)),
        }
        self._server_counts = {}
        self.to_upload = {}
        self.keys_threshold = keys_threshold

    @property
    def server_counts(self):
        return self._server_counts

    @server_counts.setter
    def server_counts(self, server_counts):
        self._server_counts = server_counts
        self.update_keys_to_upload()

    def update_keys_to_upload(self):
        for key_type, target_number in self.target_counts.items():
            num_keys = self._server_counts.get(key_type, 0)
            num_to_create = max(target_number - num_keys, 0)
            self.to_upload[key_type] = num_to_create

    def should_upload(self):
        if not self._server_counts:
            return True
        for key_type, target_number in self.target_counts.items():
            if self._server_counts.get(key_type, 0) < target_number * self.keys_threshold:
                return True
        return False

    @property
    def curve25519_to_upload(self):
        return self.to_upload.get('curve25519', 0)

    @property
    def signed_curve25519_to_upload(self):
        return self.to_upload.get('signed_curve25519', 0)
