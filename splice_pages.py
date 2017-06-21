# https://gitlab.com/Queuecumber/linux-acs-override/-/jobs/19157117/artifacts/raw/linux-headers-4.12.0-rc6-acso_4.12.0-rc6-acso-1_amd64.deb
# https://gitlab.com/Queuecumber/linux-acs-override/-/jobs/19157117/artifacts/download
# https://gitlab.com/Queuecumber/linux-acs-override/-/jobs/19157117/artifacts/browse


def make_artifact_uri(job_id):
    return 'https://gitlab.com/Queuecumber/linux-acs-override/-/jobs/{}/artifacts'.format(job_id)


def file_uri(job_id, filename):
    return '{}/raw/{}'.format(make_artifact_uri('job_id'), filename)


def download_all_uri(job_id):
    return '{}/download'.format(job_id)


def browse_all_uri(job_id):
    return '{}/browse'.format(job_id)


