# https://gitlab.com/Queuecumber/linux-acs-override/-/jobs/19157117/artifacts/raw/linux-headers-4.12.0-rc6-acso_4.12.0-rc6-acso-1_amd64.deb
# https://gitlab.com/Queuecumber/linux-acs-override/-/jobs/19157117/artifacts/download
# https://gitlab.com/Queuecumber/linux-acs-override/-/jobs/19157117/artifacts/browse

import sys
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
    return '{}/raw/{}'.format(make_artifact_uri(job_id), filename)


def image_uri(job_id, kernel_number):
    return file_uri(job_id, 'linux-image-{0}-acso_{0}-acso-1_amd64.deb'.format(kernel_number))


def headers_uri(job_id, kernel_number):
    return file_uri(job_id, 'linux-headers-{0}-acso_{0}-acso-1_amd64.deb'.format(kernel_number))


def firmware_uri(job_id, kernel_number):
    return file_uri(job_id, 'linux-firmware-image-{0}-acso_{0}-acso-1_amd64.deb'.format(kernel_number))


def download_all_uri(job_id):
    return '{}/download'.format(make_artifact_uri(job_id))


def browse_all_uri(job_id):
    return '{}/browse'.format(make_artifact_uri(job_id))


def kernel_number_from_title(kernel_title):
    kern_number = kernel_title.split(':')[0].strip()

    if kern_number.count('.') == 1:
        kern_maj_min, kern_rc = kern_number.split('-')
        kern_maj_min_patch = '{}.0'.format(kern_maj_min)

        if kern_rc is None:
            return kern_maj_min_patch
        else:
            return '{}-{}'.format(kern_maj_min_patch, kern_rc)
    else:
        return kernel_number


kernel_title = sys.argv[1]
kernel_number = kernel_number_from_title(kernel_title)

with open('kern_job_id') as f:
    job_id = f.read()

with open('index.html') as f:
    soup = BeautifulSoup(f, 'html.parser')

new_kernel_section_src = template.format(
    kernel_title=kernel_title,
    image_uri=image_uri(job_id, kernel_number),
    headers_uri=headers_uri(job_id, kernel_number),
    firmware_uri=firmware_uri(job_id, kernel_number),
    download_uri=download_all_uri(job_id),
    browse_uri=browse_all_uri(job_id)
)
new_kernel_section = BeautifulSoup(new_kernel_section_src, 'html.parser')

kernels_section = soup.select('.kernel-builds')
kernels_section[0].insert(0, new_kernel_section)

with open('index.html', mode='w') as f:
    f.write(soup.prettify())
