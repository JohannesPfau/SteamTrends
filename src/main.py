######### Example Usage #########
from utilities import run, plot_evolution_tag
import pandas as pd

if __name__ == "__main__":
    ##### Change parameters after interest #####
    run(earliest_year = 2007, latest_year = 2024, rolling_window = 5)

    ##### To plot a trend evolution graph for a given tag: #####
    plot_evolution_tag("PvE", showPlot=True, savePlot=True)

    ##### To list all tags with a minimum (relative) priority and (absolute) appearance: #####
    minimum_priority = 0.6
    minimum_games = 4000

    from utilities import trend_score_object
    tags = trend_score_object.get_considered_tags(priority_threshold=minimum_priority)['tag'].value_counts().reset_index()
    tags.columns = ['tag', 'Count']
    tags = tags[tags['Count'] > minimum_games]

    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(tags.to_string(index=False))

    ##### To save plots for all of the former tags #####
    for tag in tags['tag']:
        plot_evolution_tag(tag, showPlot=False, savePlot=True)


