# https://gitlab.com/Queuecumber/linux-acs-override/-/jobs/19157117/artifacts/raw/linux-headers-4.12.0-rc6-acso_4.12.0-rc6-acso-1_amd64.deb
# https://gitlab.com/Queuecumber/linux-acs-override/-/jobs/19157117/artifacts/download
# https://gitlab.com/Queuecumber/linux-acs-override/-/jobs/19157117/artifacts/browse

from bs4 import BeautifulSoup

template = """
    <div data-kernel="{kernel_title}">
                <h2>{kernel_title}</h2>
                <ul>
                    <li>
                        <a href="{image_uri}">Image</a>
                    </li>
                    <li>
                        <a href="{headers_uri}">Headers</a>
                    </li>
                    <li>
                        <a href="{firmware_uri}">Firmware Image</a>
                    </li>
                </ul>
                <a href="{download_uri}">Download All</a>
                <a href="{browse_uri}">Browse All</a>
            </div>
"""


def make_artifact_uri(job_id):
    return 'https://gitlab.com/Queuecumber/linux-acs-override/-/jobs/{}/artifacts'.format(job_id)


def file_uri(job_id, filename):
    return '{}/raw/{}'.format(make_artifact_uri('job_id'), filename)


def image_uri(job_id, kernel_number):
    return file_uri(job_id, 'linux-image-{}-acso_{}-acso-1_amd64.deb'.format(kernel_number))


def headers_uri(job_id, kernel_number):
    return file_uri(job_id, 'linux-headers-{}-acso_{}-acso-1_amd64.deb'.format(kernel_number))


def firmware_uri(job_id, kernel_number):
    return file_uri(job_id, 'linux-firmware-image-{}-acso_{}-acso-1_amd64.deb'.format(kernel_number))


def download_all_uri(job_id):
    return '{}/download'.format(job_id)


def browse_all_uri(job_id):
    return '{}/browse'.format(job_id)


with open('index.html') as f:
    soup = BeautifulSoup(f)

kernels_section = soup.find_all('section', class_="kernel-builds")
