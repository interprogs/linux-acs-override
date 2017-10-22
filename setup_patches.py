from subprocess import check_call
import os
import kernel
import argparse


def main(args):
    print('Arguments: {}'.format(args))
    print('Parsing build command: {0}'.format(args.kernel_string))

    kernel_version, kernel_type = kernel.KernelVersion.parse(args.kernel_string)

    if args.dryrun:
        print('DRYRUN')

    print('Setting up for kernel: {}, {}'.format(kernel_version, kernel_type))

    acso_workspace = kernel.workspace_for(kernel_version)
    print('Selected workspace {}'.format(acso_workspace.path))

    if not args.dryrun:
        os.chdir(acso_workspace.path)
        kernel.download_kernel_source(kernel_type)
        os.chdir('linux')

    kern_tag = 'v{}'.format(kernel_version)
    print('Checking out kernel tag {}'.format(kern_tag))

    if not args.dryrun:
        check_call(['git', 'checkout', kern_tag])

        print('Patching kernel')
        check_call(['git', 'apply', '../acso.patch'])
        check_call(['git', 'apply', '../build.patch'])

    print('ready to build')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Auto patch the kernel with the correct ACSO and build patches')
    parser.add_argument('--dryrun', action='store_true', help='Only simulate the patch selection process')
    parser.add_argument('kernel_string', help='String description, <kernel_number>:[mainline|stable]')
    args = parser.parse_args()
    main(args)
