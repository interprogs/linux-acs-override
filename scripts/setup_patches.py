import argparse
import contextlib
import os
from subprocess import check_call
import kernel


@contextlib.contextmanager
def pushd(path):
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def main(args):
    print('Arguments: {}'.format(args))
    print('Parsing build command: {0}'.format(args.kernel_string))

    kernel_version, kernel_type = kernel.KernelVersion.parse(args.kernel_string)

    print('Setting up for kernel: {}, {}'.format(kernel_version, kernel_type))

    acso_workspace = kernel.workspace_for(kernel_version)
    print('Selected workspace {}'.format(acso_workspace.path))

    if not args.dryrun:
        with pushd(acso_workspace.path):
            print('Downloading kernel source for {}'.format(kernel_version))
            kernel.download_kernel_source(kernel_version, kernel_type)

            with pushd('linux'):
                print('Patching kernel')
                check_call(['patch', '-p', '1', '-i', '../acso.patch'])
                check_call(['patch', '-p', '1', '-i', '../build.patch'])

        with open('workspace', 'w') as f:
            f.write('export KERNEL_WORKSPACE={}'.format(acso_workspace.path))
    else:
        print('DRYRUN')

    print('ready to build')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Auto patch the kernel with the correct ACSO and build patches')
    parser.add_argument('--dryrun', action='store_true', help='Only simulate the patch selection process')
    parser.add_argument('kernel_string', help='String description, <kernel_number>:[mainline|stable]')
    args = parser.parse_args()
    main(args)
