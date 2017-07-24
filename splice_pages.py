import sys
import json


def insert_kernel(series, kernel_number, kernel_type, build_job_id):
    kernel_definition = {
        'kernel_number': kernel_number,
        'kernel_type': kernel_type,
        'build_job_id': build_job_id
    }

    series['kernels'].append(kernel_definition)
    series['kernels'].sort(key=lambda k: k['kernel_number'], reverse=True)

    return kernel_definition


def insert_series(series, series_number, series_collapsed):
    series_definition = {
        'series_number': series_number,
        'series_collapsed': series_collapsed,
        'kernels': []
    }

    series.append(series_definition)
    series.sort(key=lambda s: s['series_number'], reverse=True)

    return series_definition


def kernel_number_from_title(kernel_title):
    kern_number = kernel_title.split(':')[0].strip()
    kern_type = kernel_title.split(':')[1].strip()

    if kern_number.count('.') == 1:
        kern_maj_min, kern_rc = kern_number.split('-')
        kern_maj_min_patch = '{}.0'.format(kern_maj_min)

        if kern_rc is None:
            return kern_maj_min_patch, kern_type
        else:
            return '{}-{}'.format(kern_maj_min_patch, kern_rc), kern_type
    else:
        return kern_number, kern_type


def kernel_series_from_number(kernel_number):
    kernel_parts = kernel_number.split('.')
    return '{}.{}'.format(kernel_parts[0], kernel_parts[1]), '{}{}'.format(kernel_parts[0], kernel_parts[1])


kernel_title = sys.argv[1]
kernel_number, kernel_type = kernel_number_from_title(kernel_title)
kernel_series, kernel_series_collapsed = kernel_series_from_number(kernel_number)

job_id = sys.argv[2]

with open('kernels.json') as f:
    kernels = json.load(f)

inserted = False
for ks in kernels['series']:
    if ks['series_number'] == kernel_series:
        insert_kernel(ks, kernel_number, kernel_type, job_id)
        inserted = True
        break

if not inserted:
    sd = insert_series(kernels['series'], kernel_series, kernel_series_collapsed)
    insert_kernel(sd, kernel_number, kernel_type, job_id)

with open('kernels.json', 'w') as f:
    json.dump(kernels, f, indent=4)
