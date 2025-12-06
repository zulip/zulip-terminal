example_sync = {
    "next_batch": "s72595_4483_1934",
    "presence": {
        "events": [
            {
                "sender": "@alice:example.com",
                "type": "m.presence",
                "content": {
                    "presence": "online"
                }
            }
        ]
    },
    "account_data": {
        "events": [
            {
                "type": "org.example.custom.config",
                "content": {
                    "custom_config_key": "custom_config_value"
                }
            }
        ]
    },
    "rooms": {
        "join": {
            "!726s6s6q:example.com": {
                "state": {
                    "events": [
                        {
                            "sender": "@alice:example.com",
                            "type": "m.room.member",
                            "state_key": "@alice:example.com",
                            "content": {
                                "membership": "join"
                            },
                            "origin_server_ts": 1417731086795,
                            "event_id": "$66697273743031:example.com"
                        }
                    ]
                },
                "timeline": {
                    "events": [
                        {
                            "sender": "@bob:example.com",
                            "type": "m.room.member",
                            "state_key": "@bob:example.com",
                            "content": {
                                "membership": "join"
                            },
                            "prev_content": {
                                "membership": "invite"
                            },
                            "origin_server_ts": 1417731086795,
                            "event_id": "$7365636s6r6432:example.com"
                        },
                        {
                            "sender": "@alice:example.com",
                            "type": "m.room.message",
                            "age": 124524,
                            "txn_id": "1234",
                            "content": {
                                "body": "I am a fish",
                                "msgtype": "m.text"
                            },
                            "origin_server_ts": 1417731086797,
                            "event_id": "$74686972643033:example.com"
                        }
                    ],
                    "limited": True,
                    "prev_batch": "t34-23535_0_0"
                },
                "ephemeral": {
                    "events": [
                        {
                            "type": "m.typing",
                            "content": {
                                "user_ids": [
                                    "@alice:example.com"
                                ]
                            }
                        }
                    ]
                },
                "account_data": {
                    "events": [
                        {
                            "type": "m.tag",
                            "content": {
                                "tags": {
                                    "work": {
                                        "order": 1
                                    }
                                }
                            }
                        },
                        {
                            "type": "org.example.custom.room.config",
                            "content": {
                                "custom_config_key": "custom_config_value"
                            }
                        }
                    ]
                }
            }
        },
        "invite": {
            "!696r7674:example.com": {
                "invite_state": {
                    "events": [
                        {
                            "sender": "@alice:example.com",
                            "type": "m.room.name",
                            "state_key": "",
                            "content": {
                                "name": "My Room Name"
                            }
                        },
                        {
                            "sender": "@alice:example.com",
                            "type": "m.room.member",
                            "state_key": "@bob:example.com",
                            "content": {
                                "membership": "invite"
                            }
                        }
                    ]
                }
            }
        },
        "leave": {}
    }
}

example_pl_event = {
    "age": 242352,
    "content": {
        "ban": 50,
        "events": {
            "m.room.name": 100,
            "m.room.power_levels": 100
        },
        "events_default": 0,
        "invite": 50,
        "kick": 50,
        "redact": 50,
        "state_default": 50,
        "users": {
            "@example:localhost": 100
        },
        "users_default": 0
    },
    "event_id": "$WLGTSEFSEF:localhost",
    "origin_server_ts": 1431961217939,
    "room_id": "!Cuyf34gef24t:localhost",
    "sender": "@example:localhost",
    "state_key": "",
    "type": "m.room.power_levels"
}

example_event_response = {
    "event_id": "YUwRidLecu"
}

example_key_upload_response = {
    "one_time_key_counts": {
        "curve25519": 10,
        "signed_curve25519": 20
    }
}

example_success_login_response = {
    "user_id": "@example:localhost",
    "access_token": "abc123",
    "home_server": "matrix.org",
    "device_id": "GHTYAJCE"
}

example_preview_url = {
    "matrix:image:size": 102400,
    "og:description": "This is a really cool blog post from matrix.org",
    "og:image": "mxc://example.com/ascERGshawAWawugaAcauga",
    "og:image:height": 48,
    "og:image:type": "image/png",
    "og:image:width": 48,
    "og:title": "Matrix Blog Post"
}
