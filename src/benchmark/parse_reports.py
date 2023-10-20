import os
from upgraider.Report import Report, DBSource, FixStatus
import jsonpickle
import argparse

def percentage(num, denom):
    if denom == 0:
        return "--"
    
    return f"{(num/denom)*100:.2f}%"

def display_perc(percent):
    # if percent is a number
    if isinstance(percent, float):
        if percent is None:
            return "--"
        
        return f"{percent:.2f}%"
    
    return f"{percent}%"

def get_display_status(status):
    
    if status == None:
        return "N/A"
    if status == FixStatus.FIXED:
        return ":white_check_mark:"
    elif status == None or status == FixStatus.NOT_FIXED:
        return ":x:"
    elif status == FixStatus.NEW_ERROR:
        return ":warning:"
    else:
        return ":question:"
    
def get_total_display(total_fixed_model, total_fixed_doc, total_examples):
    largest_total = max(total_fixed_model, total_fixed_doc)
    model_display = f"{total_fixed_model} ({percentage(total_fixed_model, total_examples)})"
    doc_display = f"{total_fixed_doc} ({percentage(total_fixed_doc, total_examples)})"

    if largest_total == total_fixed_model:
        model_display = f"**{model_display}**"

    if largest_total == total_fixed_doc:
        doc_display = f"**{doc_display}**"

    return f"Total | {total_examples} | {model_display}| {doc_display} |"

def display_detailed_stats(title, reports: dict):
    
    print(f"# {title}")
    print(f"Lib | Example | Model Only | Model + Doc |")
    print("----|---------|------------:|------------:|")
    total_examples = 0
    total_fixed_model = 0
    total_fixed_doc = 0
    
    for lib, report in reports.items():
        if report == {}:
            continue

        doc_report = report.get(DBSource.documentation.value)
        model_report = report.get("modelonly")

        for example in doc_report.snippets.keys():
            modelonly_status = model_report.snippets[example]['fix_status'] if model_report else None
            doc_status = doc_report.snippets[example]['fix_status'] if doc_report else None

            print(f"{lib} | {example} | {get_display_status(modelonly_status)} | {get_display_status(doc_status)} ")

        total_examples += len(doc_report.snippets.keys())
        total_fixed_model += model_report.num_fixed if model_report else 0
        total_fixed_doc += doc_report.num_fixed if doc_report else 0

    print(get_total_display(total_fixed_model, total_fixed_doc, total_examples))


def display_report(title, reports: dict):
    print(f"# {title}")
    print(f"| Library | # Snippets | Unique APIs | # (%) Updated | # (%) Use Ref | # (%) Fixed |")
    print(f"| --- | --: | --: | --: | --: | --: |")

   
    for lib, report in reports.items():
        if report == {}: #report might be empty in case of baseline comparisons where baseline doesn't have this lib
            continue
        
        try:
            doc_report = report[DBSource.documentation.value]

            doc_display = f"{doc_report.num_updated} ({display_perc(doc_report.percent_updated)}) | {doc_report.num_updated_w_refs} ({display_perc(doc_report.percent_updated_w_refs)}) | {doc_report.num_fixed} ({display_perc(doc_report.percent_fixed)})"
            num_snippets = doc_report.num_snippets
            num_apis = doc_report.num_apis
        except KeyError:
            doc_display = "N/A | N/A | N/A"

       
        print(f"| {lib} | {num_snippets} | {num_apis} | {doc_display} | ")

def parse_json_report(report_path: str):
    with open(report_path, 'r') as f:
        report_data = jsonpickle.decode(f.read())
        report_data['percent_updated'] = (report_data['num_updated']/report_data['num_snippets']) * 100 if report_data['num_snippets'] > 0 else 0
        report_data['percent_fixed'] = (report_data['num_fixed']/ report_data['num_updated']) * 100 if report_data['num_updated'] > 0 else 0
        report_data['percent_updated_w_refs'] = (report_data['num_updated_w_refs']/report_data['num_updated']) * 100 if report_data['num_updated'] > 0 else 0
        report = Report(**report_data)

        # sort list of snippets alphabetically
        report.snippets = {k: v for k, v in sorted(report.snippets.items(), key=lambda item: item[0])}
        return report

def parse_reports(output_dir: str):
    results = {}
    for lib_dir in os.listdir(output_dir):
        if lib_dir.startswith('.'):
            continue

        results[lib_dir] = {}
        doc_results_path = os.path.join(output_dir, lib_dir, DBSource.documentation.value, "report.json")
        if os.path.exists(doc_results_path):
            results[lib_dir][DBSource.documentation.value] = parse_json_report(doc_results_path)
        
        modelonly_results_path = os.path.join(output_dir, lib_dir, "modelonly", "report.json")
        if os.path.exists(modelonly_results_path):
            results[lib_dir]['modelonly'] = parse_json_report(modelonly_results_path)
    
    # sort results by lib alphabetically
    results = dict(sorted(results.items(), key=lambda item: item[0]))
    return results

def pp_diff(diff, percent: bool = False, lower_is_better: bool = False):

    if (percent):
        diff = round(diff, 2)

    if (diff > 0):
        display = f"+{diff}"
    elif (diff == 0):
        display = "±0"
    else:
        display = f"{diff}"
    
    if (lower_is_better):
        if (diff < 0):
            return f"**{display}**"
    else: #higher is better
        if (diff > 0):
            return f"**{display}**"

    return display
  

def compare_to_baseline(curr_results: dict, baseline: dict):
    diff_stats = {}
    for lib_name, lib_reports in curr_results.items():
        try:
            diff_stats[lib_name] = {}
            for source in [DBSource.modelonly.value, DBSource.documentation.value]:
                if (source not in lib_reports):
                    #ignore missing db sources (current run may have not used them)
                    continue

                if (lib_name not in baseline or source not in baseline[lib_name]):
                    #ignore missing db sources (previous run may have not used them)
                    continue

                curr_report = lib_reports[source]
                baseline_report = baseline[lib_name][source]
                    
                diff_stats[lib_name][source] = Report(
                    library = curr_report.library,
                    num_snippets=  curr_report.num_snippets,
                    num_apis= curr_report.num_apis,
                    num_updated= pp_diff(curr_report.num_updated - baseline_report.num_updated),
                    num_updated_w_refs= pp_diff(curr_report.num_updated_w_refs - baseline_report.num_updated_w_refs),
                    num_fixed= pp_diff(curr_report.num_fixed - baseline_report.num_fixed),
                    percent_updated= pp_diff(curr_report.percent_updated - baseline_report.percent_updated, True),
                    percent_updated_w_refs= pp_diff(curr_report.percent_updated_w_refs - baseline_report.percent_updated_w_refs, True),
                    percent_fixed= pp_diff(curr_report.percent_fixed - baseline_report.percent_fixed, True)
                )
        except KeyError:
            print(f"Skipping {lib_name} as it is not in baseline")
            #library not in baseline
            continue

    return diff_stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse and display reports')
    parser.add_argument('--outputdir', type=str, help='output folder containing results')
    parser.add_argument('--baselinedir', type=str, help='optional baseline results folder to compare to', default=None)
   

    args = parser.parse_args()

    print(f"## Interpreting stats")
    print(f"- **# (%) Updated**: Num of snippets that the model said should be updated. % in relation to total snippets")
    print(f"- **# (%) Updated w/ Refs**: Num of snippets that the model used a reference for updating. % in relation to num of updated snippets")
    print(f"- **# (%) Fixed**: Num of snippets the model was able to fix. % in relation to num of updated snippets (Reglardless of used refs)")
    print("\n")

    results = parse_reports(args.outputdir)
    display_report("Fixed Snippets Stats", results)

    display_detailed_stats("Per example results", results)

    if (args.baselinedir is not None):
        baseline = parse_reports(args.baselinedir)
        diff_stats = compare_to_baseline(results, baseline)
        display_report("Comparison to Baseline", diff_stats)

