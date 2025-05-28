
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import SparsePCA

import trend_scores_computation

global general_trend_score, earliest_complete_year, recent_trend_score, high_priority_trend_score, high_priority_recent_trend_score, combined_recent_trend_score, trend_score_object
combined_recent_trend_score = 0

def run(earliest_year = 2007, latest_year = 2024, rolling_window = 5): # number of years considered for the recent trend score and high-priority recent_trend_score
    ######## Compute trend scores
    global general_trend_score, earliest_complete_year, recent_trend_score, high_priority_trend_score, high_priority_recent_trend_score, combined_recent_trend_score, trend_score_object

    earliest_complete_year = earliest_year + rolling_window

    steam_tags = pd.read_csv('.\data\steam_tags.csv')

    trend_score_object = trend_scores_computation.TrendScores(steam_tags, earliest_year, latest_year, rolling_window)

    general_trend_score, recent_trend_score = trend_score_object.trend_scores(0)

    high_priority_trend_score, high_priority_recent_trend_score = trend_score_object.trend_scores(0.6)

    # the combined recent trend score is defined by the coefficients obtained with the sparse PCA
    combined_recent_trend_score = 0.82 * recent_trend_score + 0.57 * high_priority_recent_trend_score

######### Apply the sparse PCA #########

def apply_sparse_PCA():

    # filter for years with complete data for all trend scores (the recent scores have fewer complete years because of the rolling window)
    df1 = general_trend_score.loc[earliest_complete_year:]
    df2 = recent_trend_score
    df3 = high_priority_trend_score.loc[earliest_complete_year:]
    df4 = high_priority_recent_trend_score
    
    # melt each dataframe into long format
    melted_df1 = df1.reset_index().melt(id_vars='year', var_name='Tag', value_name='general')
    melted_df2 = df2.reset_index().melt(id_vars='year', var_name='Tag', value_name='recent')
    melted_df3 = df3.reset_index().melt(id_vars='year', var_name='Tag', value_name='high-priority')
    melted_df4 = df4.reset_index().melt(id_vars='year', var_name='Tag', value_name='high-priority recent')
    
    
    # merge the melted dataframes
    merged_df = pd.merge(melted_df1, melted_df2, on=['year', 'Tag'])
    merged_df = pd.merge(merged_df, melted_df3, on=['year', 'Tag'])
    merged_df = pd.merge(merged_df, melted_df4, on=['year', 'Tag'])
    
    # set a multi-index of Tag and Year
    final_df = merged_df.set_index(['Tag', 'year'])
    
    
    # extract the data for the spase PCA
    data = final_df[['general', 'recent', 'high-priority', 'high-priority recent']].values
    
    # apply the sparse PCA
    sparse_pca = SparsePCA(n_components=3)
    sparse_pca.fit_transform(data)
    print("Sparse PCA Principal Components:\n", sparse_pca.components_)
    
    return sparse_pca


######### Plot trend scores #########

def plot_evolution_tag(tag, showPlot=True, savePlot=True):
    
    tag_evolution = pd.concat([general_trend_score[tag], recent_trend_score[tag],
                               high_priority_trend_score[tag], high_priority_recent_trend_score[tag]], axis = 1)
    
    tag_evolution.columns = ['general', 'recent', 'high-priority', 'high-priority recent']
    
    ax = tag_evolution.plot(title = tag, yticks = [])
    ax.set_yticks(np.linspace(-0.5, 0.5, num=5))
    
    ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    ax.set_ylabel("Cohen's h")

    if savePlot:
        plt.savefig('./results/'+tag+'.png')

    if showPlot:
        plt.show()
    plt.close()
    
   

def plot_evolution_tag_after_pca(tag):
    
    tag_evolution = pd.concat([general_trend_score[tag], combined_recent_trend_score[tag], high_priority_trend_score[tag]], axis = 1)
    
    tag_evolution.columns = ['general', 'combined recent', 'high-priority']
    
    ax = tag_evolution.plot(title = tag, yticks = [])
    ax.set_yticks(np.linspace(-0.5, 0.5, num=5))
    
    ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    ax.set_ylabel("Cohen's h")

    plt.show()
    plt.close()



def plot_general_trend_scores(tags_list):
    
    tag_evolution = pd.concat([general_trend_score[tag] for tag in tags_list], axis = 1)
   
    ax = tag_evolution.plot(yticks = [],  colormap="coolwarm")
    ax.set_yticks(np.linspace(-0.5, 0.5, num=5))
    
    ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    
    ax.set_ylabel("Cohen's h")

    plt.show()
    plt.close()



######### Plot trend increases #########
   
def longest_consecutive_positive_growth(trend_score = combined_recent_trend_score, plot_hist = True):
    """
    

    Parameters
    ----------
    trend_score : Pandas dataframe
        one of general_trend_score, recent_trend_score, high_priority_trend_score, high_priority_recent_trend_score.
    plot_hist : Boolean, optional
        Plots the histogram of the maximal streak durations. The default is True.

    Returns
    -------
    streak_length : Pandas dataframe
        The index is the tags. One column gives the duration of a longest streak, the other gives the year the streak ended.

    """
    
    streak_length_dict = {}
    for tag in trend_score.columns:
        
        max_streak = 0
        current_streak = 0
        current_year = earliest_complete_year - 1
        last_year_streak = 0
        
        for value_year in trend_score[tag]:
            
            current_year += 1
            
            if value_year > 0: # if the Cohen's h is still positive, we increase the streak duration
                current_streak += 1
            
            else: # else we check whether this streak is the longest one seen so far
                if current_streak > max_streak:
                    last_year_streak = current_year
                    max_streak = current_streak
            
                current_streak = 0
            
        streak_length_dict[tag] = [max_streak, last_year_streak]
        
    streak_length = pd.DataFrame().from_dict(streak_length_dict, orient = 'index', columns = ['max consecutive years', 'last year streak']).sort_values('max consecutive years', ascending=False)
        
    if plot_hist:

        streak_length['max consecutive years'].hist(bins=streak_length['max consecutive years'].max()+1, density=True)
        
    return streak_length




def generate_random_samples(trend_score = combined_recent_trend_score, nb_fictive_tags = 10):
    """
    

    Parameters
    ----------
    trend_score : Pandas dataframe
        one of general_trend_score, recent_trend_score, high_priority_trend_score, high_priority_recent_trend_score.
    nb_false_tags : Int, optional
        The number of fictive tags to generate randomly. The default is 10.

    Returns
    -------
    Pandas dataframe. The index is the same as with trend_score. The number of columns is nb_fictive_tags
        The values are randomly generated from the values in trend_score

    """
    
    values = trend_score.melt().dropna()
    
    years = pd.DataFrame(trend_score.index)
    
    for i in range(1, nb_fictive_tags + 1):
        years[f'fictive_tag_{i}'] = np.random.choice(values['value'], size=len(years), replace=True)
    
    return years.set_index('year')

    



def histograms_comparison():
    
    true_distribution = longest_consecutive_positive_growth(plot_hist=False)
    
    fictive_distribution = longest_consecutive_positive_growth(trend_score = generate_random_samples(nb_fictive_tags=1000), plot_hist=False)
    
    true_distribution.columns=['observed distribution','last year streak']
    fictive_distribution.columns=['distribution obtained by independent sampling','last year streak']
    
    both_distributions = pd.concat([true_distribution, fictive_distribution])
    
    both_distributions = both_distributions.reset_index()[['observed distribution', 'distribution obtained by independent sampling']]
    
    both_distributions.plot.hist(bins=11, alpha=0.5, density=True)
