import kernel
import argparse


def main(args):
    print('Adding new workspace for version {} at {}'.format(args.version, args.path))
    version, _ = kernel.KernelVersion.parse(args.version)
    version.save()

    workspace = kernel.Workspace(args.path, version)
    workspace.save()

    kernel.Workspace.load()

    print('Checking workspace existence, this should match what you just added')
    wsf = kernel.workspace_for(version)
    print('{}, {}'.format(wsf.path, wsf.version))

    print('Done')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', help='Path to workspace directory')
    parser.add_argument('--version', help='Version string for matching kernel version')
    args = parser.parse_args()
    main(args)
