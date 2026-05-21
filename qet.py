import argparse


def parser_generator():
    parser = argparse.ArgumentParser(description="QET")
    parser.add_argument('--project_path', type=str, default='Benchmark/exact_reciprocal_gate')

    return parser.parse_args()


def run_qet(project_path):
    return


if __name__ == "__main__":
    args = parser_generator()

    results = run_qet(args.project_path)
