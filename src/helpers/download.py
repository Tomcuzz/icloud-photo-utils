"""Handles file downloads with retries and error handling"""

import os
import socket
import time
import logging
import datetime
from tzlocal import get_localzone
from requests.exceptions import ConnectionError  # pylint: disable=redefined-builtin
from src.pyicloud_ipd.exceptions import PyiCloudAPIResponseError

def update_mtime(created: datetime.datetime, download_path):
    """Set the modification time of the downloaded file to the photo creation date"""
    if created:
        created_date = None
        try:
            created_date = created.astimezone(
                get_localzone())
        except (ValueError, OSError):
            # We already show the timezone conversion error in base.py,
            # when generating the download directory.
            # So just return silently without touching the mtime.
            return
        set_utime(download_path, created_date)


def set_utime(download_path, created_date):
    """Set date & time of the file"""
    ctime = time.mktime(created_date.timetuple())
    os.utime(download_path, (ctime, ctime))

def mkdirs_for_path(download_path: str) -> bool:
    """ Creates hierarchy of folders for file path if it needed """
    try:
        # get back the directory for the file to be downloaded and create it if
        # not there already
        download_dir = os.path.dirname(download_path)
        os.makedirs(name = download_dir, exist_ok=True)
        return True
    except OSError:
        logging.error(
            "Could not create folder %s",
            download_dir,
        )
        return False

def mkdirs_for_path_dry_run(download_path: str) -> bool:
    """ DRY Run for Creating hierarchy of folders for file path """
    download_dir = os.path.dirname(download_path)
    if not os.path.exists(download_dir):
        logging.debug(
            "[DRY RUN] Would create folder hierarchy %s",
            download_dir,
        )
    return True

def download_response_to_path(
        response,
        download_path: str,
        created_date: datetime.datetime) -> bool:
    """ Saves response content into file with desired created date """
    temp_download_path = download_path + ".part"
    with open(temp_download_path, "wb") as file_obj:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file_obj.write(chunk)
    os.rename(temp_download_path, download_path)
    update_mtime(created_date, download_path)
    return True

def download_response_to_path_dry_run(
        _response,
        download_path: str,
        _created_date: datetime.datetime) -> bool:
    """ Pretends to save response content into a file with desired created date """
    logging.info(
        "[DRY RUN] Would download %s",
        download_path,
    )
    return True

# pylint: disable-msg=too-many-arguments
def download_media(icloud, photo, download_path, size) -> bool:
    """Download the photo to path, with retries and error handling, returns True if download is successful."""
    if not mkdirs_for_path(download_path):
        return False

    for retries in range(icloud.app.configs.max_retries):
        try:
            photo_response = photo.download(size)
            if photo_response:
                return download_response_to_path(photo_response, download_path, photo.created)

            logging.error(
                "Could not find URL to download %s for size %s",
                photo.filename,
                size
            )
            break

        except (ConnectionError, socket.timeout, PyiCloudAPIResponseError) as ex:
            if "Invalid global session" in str(ex):
                if icloud.api:
                    icloud.api.authenticate()
                logging.error("Session error")
            else:
                # you end up here when p.e. throttling by Apple happens
                wait_time = icloud.app.configs.wait_seconds * (retries + 1) * (retries + 1)
                logging.error(
                    "Error downloading %s, retrying after %s seconds...",
                    photo.filename,
                    wait_time
                )
                time.sleep(wait_time)

        except IOError:
            logging.error(
                "IOError while writing file to %s. " +
                "You might have run out of disk space, or the file " +
                "might be too large for your OS. " +
                "Skipping this file...", 
                download_path
            )
            break
    else:
        logging.error(
            "Could not download %s. Please try again later.", 
            photo.filename,
        )

    return False
