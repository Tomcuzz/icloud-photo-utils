""" iCloud api connection helpers """
from src.pyicloud_ipd import utils, base # pylint: disable=import-error
from src.helpers.settings import Settings # pylint: disable=import-error

class ICloud(object):
    """ iCloud api connection class """
    def __init__(self, configs:Settings) -> None:
        self.configs = configs
        self.api = self.setup_api()
        self.auth_trusted_devices = None
        self.selected_auth_trusted_device = None

    def setup_api(self) -> base.PyiCloudService:
        """ Setup api connection """
        if self.configs.username and self.has_password():
            try:
                passwd = utils.get_password_from_keyring(self.configs.username)
                self.api = base.PyiCloudService(
                    "com",
                    self.configs.username.strip(),
                    passwd.strip()
                )
                return self.api
            except base.NoStoredPasswordAvailable:
                print('iCloud password not avalible')
        return None

    def update_username(self):
        """ Notify that username was updated """
        self.api = self.setup_api

    @property
    def has_username(self) -> bool:
        """ Check if have saved username """
        return self.configs.username != ""

    @property
    def has_password(self) -> bool:
        """ Check if have saved password """
        return utils.password_exists_in_keyring(self.configs.username)

    @property
    def needs_2fa_setup(self) -> bool:
        """ Check if 2 Factor Auth Setup needed"""
        if self.api is None:
            return False
        return self.api.requires_2sa

    def get_trusted_devices(self) -> list:
        """ List Trused 2fa devices """
        self.auth_trusted_devices = self.api.trusted_devices
        trusted_devices = []
        for i, device in enumerate(self.auth_trusted_devices):
            trusted_devices[i] = device.get(
                    'deviceName',
                    "SMS to %s" % device.get('phoneNumber'))
        return self.api.trusted_devices

    def send_2fa_code(self, device:int) -> bool:
        """ Request 2fa code send """
        if self.auth_trusted_devices is None:
            return False
        if len(self.auth_trusted_devices) < device:
            return False
        self.selected_auth_trusted_device = self.auth_trusted_devices[device]
        return self.api.send_verification_code(self.selected_auth_trusted_device)

    def validate_2fa_code(self, code:str) -> bool:
        """ Validate 2fa code """
        if not self.auth_trusted_devices or not self.selected_auth_trusted_device:
            return False
        return self.api.validate_verification_code(self.selected_auth_trusted_device, code)
