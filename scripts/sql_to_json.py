import argparse
import json

import kernel


def main(args):
    kernel_version, kernel_type = kernel.KernelVersion.parse(args.kernel_string)
    kernel_series = kernel.KernelSeries.from_version(kernel_version)

    kernel_version.save()
    kernel_series.save()

    built_kernel = kernel.BuiltKernel(version=kernel_version,
                                      type=kernel_type,
                                      build_job_id=args.job_id,
                                      series=kernel_series)

    try:
        built_kernel.save()
    except Exception as e:
        print('WARNING: {}'.format(e))

    all_kernels = kernel.built_kernels_dict()

    with open('kernel.json', 'w') as f:
        json.dump(all_kernels, f, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build "JSON API cache" for ACSO kernel site')
    parser.add_argument('kernel_string', help='String description, <kernel_number>:[mainline|stable]')
    parser.add_argument('job_id', help='ID of CI job that built the kernel')
    args = parser.parse_args()
    main(args)
