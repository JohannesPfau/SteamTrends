
import numpy as np

######## Cohen's h computation

def arcsin_transfo(proportion):
    return 2 * np.arcsin(np.sqrt(proportion))

def compute_cohen_h(prop1, prop2):
    return arcsin_transfo(prop1) - arcsin_transfo(prop2)



def cohen_h_previous_years(proportion_one_year, proportion_previous_years):
    """
    computes cohen h of a specific year, with respect to the five years before

    """
    # Create the result DataFrame by applying the function element-wise
    proportion_cohen_h = proportion_one_year.copy()
    
    for tag in proportion_cohen_h.columns:
        proportion_cohen_h[tag] = proportion_one_year[tag].combine(proportion_previous_years[tag], compute_cohen_h)
        
    return proportion_cohen_h



def cohen_h_all_years(proportion_one_year, average_all_years):
    """
    computes cohen h of a specific year, with respect to all years

    """
    
    proportion_cohen_h = proportion_one_year.copy()
    
    for tag in proportion_cohen_h.columns:
    
        proportion_cohen_h[tag] = proportion_cohen_h[tag].apply(lambda x: compute_cohen_h(x, average_all_years[tag]))
        
    return proportion_cohen_h

###### class definition

class TrendScores:
    
    def __init__(self,
                 tags_dataset,
                 earliest_year,
                 latest_year,
                 rolling_window):
        """
        

        Parameters
        ----------
        tags_dataset : Pandas dataframe,
            Contains the columns: tag, game_id, nb_players, year.
        The three other variables are INT. They give earliest year to consider, the most recent year,
        and the rolling window size for computing recent trend scores.

        """
        
        self.tags_dataset = tags_dataset[(tags_dataset['year']>= earliest_year) & (tags_dataset['year']<= latest_year)]
        self.tags_dataset['priority'] = self.tags_dataset['nb_players'] / self.tags_dataset.groupby('game_id')['nb_players'].transform('max')

        self.rolling_window = rolling_window 
        self.earliest_complete_year = earliest_year + rolling_window

    def _nb_games_year(self, year, tags_considered):
        # tags_considered has the same columns as self.tags_dataset, potentially with fewer rows
        
        return len(tags_considered[tags_considered['year'] == year]['game_id'].drop_duplicates())
    
    
    def _tags_proportions(self, tags_considered):
        """
        

        Parameters
        ----------
        tags_considered : Pandas dataframe
            Contains the columns: tag, game_id, priority, year. It is like self.tags_dataset, potentially with fewer rows

        Returns
        -------
        tags_proportion_games_per_year : Pandas dataframe
            Rows are years, and columns are tags. The values are the proportion of games released at given year with a given tag
        tags_average_proportion : Pandas dataframe
            Rows are tags. Values are the normalised average proportion of games with a given tags over all years
        tags_average_proportion_previous_years : Pandas dataframe
            Rows are years, and columns are tags. The values are the proportion of games released with a given tag over the past self.rolling_window years

        """
        
        tags_nb_games_per_year = tags_considered.groupby(['tag','year']).count().reset_index()
        tags_nb_games_per_year = tags_nb_games_per_year.pivot(index='year',columns='tag', values='game_id').fillna(0)
        # tags_nb_games_per_year gives for each year Y and each tag T how many games with T were released at year Y
        
        nb_games_per_year = tags_nb_games_per_year.index.to_series().apply(lambda x: self._nb_games_year(x, tags_considered))
    
    
        #for each tag, for each year, gives the proportion of games released that year on games with this tag
        #over all games released that year
        tags_proportion_games_per_year = tags_nb_games_per_year.div(nb_games_per_year, axis=0)
        
        #for each tag, normalised average proportion of games released with this tag
        tags_average_proportion = tags_proportion_games_per_year.mean()
        
        #for each tag, for each year, normalised average proportion of games released with this tag during the recent years
        tags_average_proportion_previous_years = tags_proportion_games_per_year.copy()
        
        
        #apply the rolling mean calculation column-wise
        for tag in tags_proportion_games_per_year.columns:
            tags_average_proportion_previous_years[tag] = tags_proportion_games_per_year[tag].rolling(
                window=self.rolling_window, min_periods=self.rolling_window).mean()
            
            
        return tags_proportion_games_per_year, tags_average_proportion, tags_average_proportion_previous_years
        
    


    def trend_scores(self, priority_threshold = 0):
        
        tags_considered = self.tags_dataset[self.tags_dataset['priority'] >= priority_threshold]
        
        tags_proportion_games_per_year, tags_average_proportion, tags_average_proportion_previous_years = self._tags_proportions(tags_considered)
         
        general_trend_score = cohen_h_all_years(tags_proportion_games_per_year, tags_average_proportion)
        
        # we only keep the years for which we have complete data, since we apply a rolling window
        recent_trend_score = cohen_h_previous_years(tags_proportion_games_per_year, tags_average_proportion_previous_years).loc[self.earliest_complete_year:]
        
        return general_trend_score, recent_trend_score

    def get_considered_tags(self, priority_threshold = 0):
        return self.tags_dataset[self.tags_dataset['priority'] >= priority_threshold]