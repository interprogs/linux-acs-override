import json
import kernel
import argparse


def main(args):
    print('Dumping built kernel data to {}'.format(args.out))
    all_kernels = kernel.db_to_dict()
    with open(args.out, 'w') as f:
        json.dump(all_kernels, f, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dump contents of built kernel tables to JSON')
    parser.add_argument('out', help='Path to output JSON file')
    args = parser.parse_args()
    main(args)
