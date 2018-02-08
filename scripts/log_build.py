import argparse
import kernel


def main(args):
    print('Storing successful build of {} for job {}'.format(args.kernel_string, args.job_id))

    kernel_version, kernel_type = kernel.KernelVersion.parse(args.kernel_string)
    kernel_series = kernel.KernelSeries.from_version(kernel_version)

    kernel_version.save()
    kernel_series.save()

    built_kernel = kernel.BuiltKernel(version=kernel_version,
                                      type=kernel_type,
                                      build_job_id=args.job_id,
                                      kernel_series=kernel_series,
                                      workspace=kernel.workspace_for(kernel_version))

    try:
        built_kernel.save()
    except Exception as e:
        print('WARNING: {}'.format(e))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Log a successful build to the database')
    parser.add_argument('kernel_string', help='String description, <kernel_number>:[mainline|stable]')
    parser.add_argument('job_id', help='ID of CI job that built the kernel')
    args = parser.parse_args()
    main(args)
