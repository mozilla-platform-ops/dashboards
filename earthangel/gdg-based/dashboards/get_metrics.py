#!/usr/bin/env python3

import json
import argparse

def extract_metrics_from_dashboard(json_file, verbose=False):
    """
    Extract metric names from Grafana dashboard JSON file.
    """
    metrics = set()

    try:
        with open(json_file, 'r') as file:
            dashboard = json.load(file)

        if 'annotations' in dashboard:
            for annotation in dashboard['annotations']['list']:
                # print(annotation['datasource']['type'])
                if annotation['datasource']['type'] == 'influxdb':
                    query = annotation['query']
                    metrics.update(extract_metrics_from_query(query))
                    if verbose:
                        print(f"Found annotation query: {query}")

        # Iterate through panels to find targets with queries
        for panel in dashboard.get('panels', []):
            for target in panel.get('targets', []):
                query = target.get('query')
                measurement = target.get('measurement')

                if measurement:
                    # remove all quotes from the measurement name (not just the first and last)
                    measurement = measurement.replace('"', '')
                    metrics.add(measurement)
                    if verbose:
                        print(f"Found measurement: {measurement}")
                if query:
                    metrics.update(extract_metrics_from_query(query))
                    if verbose:
                        print(f"Found target query: {query}")

    except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        print(f"Error: {e}")

    return metrics


def extract_metrics_from_query(query):
    """
    Extract potential metric names from a query string.

    e.g. SELECT mean("pendingTasks") / (mean("running")) as "runner load" FROM six_month."tc_queue_exec" WHERE $timeFilter AND "provisionerId" = 'terraform-packet' AND "workerType" != '' GROUP BY time(20m), "workerType", "provisionerId" fill(1)

    """
    metrics = set()
    # print(query)

    # split query on word boundaries, scan until we find "FROM", the metric should be right after that
    query = query.split()
    for i, word in enumerate(query):
        if word == "FROM":
            metric = query[i + 1].strip('"')
            # remove all quotes and backslashes from the metric name
            metric = metric.strip('"')
            metrics.add(metric)
            break
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Extract metric names from Grafana dashboard JSON.")
    parser.add_argument('file', type=str, help="Path to the Grafana dashboard JSON file")
    parser.add_argument('-v', '--verbose', action='store_true', help="Increase output verbosity")
    args = parser.parse_args()

    metrics = extract_metrics_from_dashboard(args.file, args.verbose)

    if metrics:
        if args.verbose:
            print()
        print("Metrics found in the dashboard:")
        for metric in sorted(metrics):
            print(metric)
    else:
        print("No metrics found.")

if __name__ == "__main__":
    main()
