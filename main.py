import pandas as pd
from floodlight.io.datasets import StatsBombOpenDataset
import matplotlib.pyplot as plt
from floodlight.vis.pitches import plot_football_pitch
import ast
import matplotlib.pyplot as plt
import numpy as np
from floodlight.core.xy import XY
from floodlight.vis.positions import plot_positions, plot_trajectories
import imageio
import os
import seaborn as sns
import json


dataset = StatsBombOpenDataset()

HOME_TEAM = 'Tottenham Hotspur'
AWAY_TEAM = 'Liverpool'

match = dataset.get("Champions League", "2018/2019", HOME_TEAM + " vs. " + AWAY_TEAM)


class Visualize:

    def __manipulate_data(df) -> pd.DataFrame:
        """Manipulates the data to make it easier to work with"""
        df["qualifier"] =  df["qualifier"].map(lambda d : ast.literal_eval(d))
        df = df.join(pd.DataFrame(df["qualifier"].to_dict()).T)
        #df = df.drop(columns=["qualifier"])
        return df

    def __plot_event(event, index):
        """Plots an event"""

        event_name = event['event_name']
        event_team = event['team_name']


        player_name = event['player_name']
        at_x = event['at_x'] if event_team == AWAY_TEAM else 120 - event['at_x']
        at_y = event['at_y'] if event_team == AWAY_TEAM else 90 - event['at_y']
        player_color = 'red' if event_team == AWAY_TEAM else 'blue'
        player_pos = XY(np.array([[at_x, at_y]]))


        ax = plt.subplots()[1]
        plot_football_pitch(xlim=(0,120), ylim=(0,90), length=120, width=90, unit='m',
                        color_scheme='standard', show_axis_ticks=False, ax=ax)


        if event['event_name'] == 'Pass':
            to_x = event['to_x'] if event_team == AWAY_TEAM else 120 - event['to_x']
            to_y = event['to_y'] if event_team == AWAY_TEAM else 90 - event['to_y']
            to_pos = XY(np.array([[to_x, to_y]]))
            at_to = XY(np.array([[at_x, at_y], [to_x, to_y]]))

            plot_trajectories(xy=at_to, start_frame=0, end_frame=2, ball=False, ax=ax)
            if 'recipient' in str(event['pass']):
                plot_positions(xy= to_pos, frame=0, ball=True, ax=ax, color="yellow")
            else:
                plot_positions(xy= to_pos, frame=0, ball=True, ax=ax, color="red")
        elif event['event_name'] == 'Carry':
            to_x = event['to_x'] if event_team == AWAY_TEAM else 120 - event['to_x']
            to_y = event['to_y'] if event_team == AWAY_TEAM else 90 - event['to_y']
            to_pos = XY(np.array([[to_x, to_y]]))
            at_to = XY(np.array([[at_x, at_y], [to_x, to_y]]))

            plot_trajectories(xy=at_to, start_frame=0, end_frame=2, ball=False, ax=ax)
            plot_positions(xy= to_pos, frame=0, ball=True, ax=ax, color="yellow")
        elif event['event_name'] == 'Shot':
            to_x = event['to_x'] if event_team == AWAY_TEAM else 120 - event['to_x']
            to_y = event['to_y'] if event_team == AWAY_TEAM else 90 - event['to_y']
            to_pos = XY(np.array([[to_x, to_y]]))
            at_to = XY(np.array([[at_x, at_y], [to_x, to_y]]))

            plot_trajectories(xy=at_to, start_frame=0, end_frame=2, ball=False, ax=ax)
            plot_positions(xy= to_pos, frame=0, ball=True, ax=ax, color="yellow")
        
        plot_positions(xy= player_pos, frame=0, ball=False, ax=ax, color = player_color)
        ax.text(player_pos.x - len(player_name)/2, player_pos.y + 2, str(player_name), fontsize=5, color="black")
        ax.text(0, 0, str(event_name), fontsize=7, color="black")

        if not os.path.exists("images"):
            os.makedirs("images")
        
        plt.savefig("images/event"+ str(index) + ".png", dpi = 200)
        ax.clear()
        plt.close()

    def __plot_passes_of_player(player, df):
        """Plots all passes of a player"""
        ax = plt.subplots()[1]
        plot_football_pitch(xlim=(0,120), ylim=(0,90), length=120, width=90, unit='m',
                        color_scheme='standard', show_axis_ticks=False, ax=ax)

        data = Visualize.__manipulate_data(df[(df['event_name'] == 'Pass') & (df['player_name'] == player)])

        successful_passes = 0
        fail_passes = 0
        low_pass = 0
        high_pass = 0

        for index, event in data.iterrows():
            at_x = event['at_x']
            at_y = event['at_y']
            to_x = event['to_x']
            to_y = event['to_y']
            at_to = XY(np.array([[at_x, at_y], [to_x, to_y]]))
            plot_positions(xy = at_to, frame = 0, ball = False, ax = ax, color = "blue")
            if event['outcome'] == 0:
                plot_trajectories(xy = at_to, start_frame = 0, end_frame = 2, ball = False, ax = ax, color = "red")
                successful_passes = successful_passes + 1
            else:
                plot_trajectories(xy = at_to, start_frame = 0, end_frame = 2, ball = False, ax = ax, color = "yellow")
                fail_passes = fail_passes + 1
            if 'Ground Pass' in str(event['pass']):
                low_pass = low_pass + 1
            if 'Low Pass' in str(event['pass']):
                low_pass = low_pass + 1
            if 'High Pass' in str(event['pass']):
                high_pass = high_pass + 1

        at_x = data['at_x']
        at_y = data['at_y']

        sns.kdeplot(x = at_x, y = at_y, fill = True, 
        thresh=.05, ax = ax, alpha = .5, cmap = 'magma')

        ax.text(1, 2, player
        + '\n' +'Success pass count:' + str(successful_passes) + '\n' +
        'Fail pass count:' + str(fail_passes), fontsize=7, color="black")
        ax.text(1, -10, 'Low pass count:' + str(low_pass) + '\n' +
        'High pass count:' + str(high_pass), fontsize=7, color="black")

        plt.show()

    def __make_gif(id, image_ids):
        """Creates a gif of all the events in the same possession"""
        filenames = ["images/event"+ str(index) + ".png" for index in image_ids]
        images = []
        for filename in filenames:
            images.append(imageio.imread(filename))
        imageio.mimsave("images/movie" + str(id) +".gif", images, duration=0.5)
        print("---Gif created under images folder---")
        os.system("rm images/event*.png")

    @staticmethod
    def plot_goals(match):
        """Plots all goals in a match"""

        ## For loop for all halfs
        for index, halfs in enumerate(match):
            df = Visualize.__manipulate_data(halfs.events)

            ## For loop for all goals
            for goal_index, goal_event in df[(df['outcome'] > 0) & (df['event_name'] == 'Shot')].iterrows():
                posession_index_list = []

                ## For loop for all events in the same possession
                for event_index, event in df[df['possession'] == int(goal_event['possession'])].iterrows():
                    Visualize.__plot_event(event, event_index)
                    posession_index_list.append(event_index)
                
                Visualize.__make_gif(goal_index, posession_index_list)

    @staticmethod
    def plot_passes(match):
        """Plots passes of a player"""

        data = pd.concat([halfs.events for halfs in match])
        indexed_player_names = {index: name for index, name in 
            enumerate(data.dropna(subset=['player_name'])['player_name'].unique())}

        for index, name in indexed_player_names.items():
            print(str(index) + ': ' + name)

        player_index = input("Enter player index: ")
        player_name = indexed_player_names[int(player_index)]
        
        Visualize.__plot_passes_of_player(player_name, data)

    @staticmethod
    def plot_distance_of_players_to_center_at_goal(match):
        """Plots the distance of players to the center of the each other at the moment of the goal"""
        def select_goal_event(match):
            data = {}
            for index, halfs in enumerate(match):
                df = halfs.events

                ## Print all goal events
                for event_index, goal_event in df[(df['outcome'] > 0) & (df['event_name'] == 'Shot')].iterrows():
                    print("Event index:",str(event_index),
                    ", Scorer:", str(goal_event['player_name']),
                    "at",str(goal_event['minute'])+":"+str(goal_event['second']))
                    data[event_index] = goal_event

            input_index = input("Choose goal event index:")
            try:
                return data[int(input_index)]
            except:
                print("Wrong input")
                exit()

        def manipulate_location_data(loc_data):
            try:
                string = "{'freeze_frame"+(str(loc_data['qualifier']).split('freeze_frame')[1])
            except:
                print("No location data for this event")
                exit
            
            for r in (("'", '"'), ("True", '"True"'), ("False", '"False"')):
                string = string.replace(*r)

            string = string[:-1]
            js = json.loads(string)

            dff = pd.json_normalize(js, record_path = ['freeze_frame'])
            dff['x'], dff['y'] = dff['location'].str[0], dff['location'].str[1]
            
            return dff

        def find_location_of_players(loc_data, isTeammate):
            return loc_data[loc_data['teammate'] == isTeammate]['x'], loc_data[loc_data['teammate'] == isTeammate]['y']

        def calc_distance(x1, y1, x2, y2):
            return np.sqrt((x1-x2)**2 + (y1-y2)**2)

        def on_click(pick_event, x1, y1):
            index = pick_event.ind[0]
            x, y = pick_event.artist.get_offsets()[index]

            at_to = XY(np.array([[x, y], [x1, y1]]))
            plot_trajectories(xy=at_to, start_frame=0, end_frame=2, ball=False, ax=ax, color="red")

            distance = calc_distance(x, y, x1, y1)
            distance_text = ax.text(1, 2, "Distance in meter: " + str(round(distance, 2)), fontsize=7, color="black")
            
            player_name = ax.text(1, -3, "Player: " + str(dff.iloc[index]['player.name']), fontsize=7, color="black")

            fig.canvas.draw()
            fig.canvas.flush_events()
            ax.lines.pop()
            player_name.remove()
            distance_text.remove()
        
        def plot_initial():
            plot_football_pitch(xlim=(0,120), ylim=(0,90), length=120, width=90, unit='m',
                                color_scheme='standard', show_axis_ticks=False, ax=ax)

            plot_positions(XY(np.array([[center_mate_x, center_mate_y]])), frame = 0, 
                                ball = False, ax = ax, color = "yellow", marker='*')

            mate_xy = XY(np.array([np.array([mate_x, mate_y]).T.flatten()]))
            plot_positions(xy = mate_xy, frame = 0, ball = False, ax = ax, color = "blue", picker = True)

            opp_xy = XY(np.array([np.array([opp_x, opp_y]).T.flatten()]))
            plot_positions(xy = opp_xy, frame = 0, ball = False, ax = ax, color = "red")
            
            fig.canvas.mpl_connect('pick_event', lambda pick_event: on_click(pick_event, center_mate_x, center_mate_y))

            plt.show()
        
        event = select_goal_event(match)
        dff = manipulate_location_data(event)
        
        mate_x, mate_y = find_location_of_players(dff, isTeammate='True')
        opp_x, opp_y = find_location_of_players(dff, isTeammate='False')
        
        center_mate_x, center_mate_y = mate_x.mean(), mate_y.mean()
        center_opp_x, center_opp_y = opp_x.mean(), opp_y.mean()
        
        fig,ax = plt.subplots()

        plot_initial()
        

inp = input(
    "1: Pass Heat Map of a Player\n" +
    "2: Make a Goal Event Gif\n" +
    "3: Distance of players to center at goal\n")

while inp != "exit":
    if inp == "1":
        Visualize.plot_passes(match)
    elif inp == "2":
        Visualize.plot_goals(match)
    elif inp == "3":
        Visualize.plot_distance_of_players_to_center_at_goal(match)
    else:
        print("Wrong input")

    inp = input(
    "1: Pass Heat Map of a Player\n" +
    "2: Make a Goal Event Gif\n" +
    "3: Distance of players to center at goal\n")