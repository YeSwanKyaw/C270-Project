import tkinter as tk


class PlayerStats:

    def __init__(self, name):

        self.name = name

        self.games_played = 0
        self.wins = 0
        self.losses = 0

        self.local_wins = 0
        self.ai_wins = 0

        self.total_spaces = 0


    # Function called after every game
    def update_game(self, result, mode, spaces):

        self.games_played += 1

        self.total_spaces += spaces


        if result == "win":

            self.wins += 1

            if mode == "local":
                self.local_wins += 1

            elif mode == "ai":
                self.ai_wins += 1


        else:

            self.losses += 1



    def get_win_rate(self):

        if self.games_played == 0:
            return 0

        return (self.wins / self.games_played) * 100




class StatsScreen:


    def __init__(self, root, player):

        self.root = root
        self.player = player


        root.title("Answer and Conquer - Stats")

        root.geometry("450x500")


        title = tk.Label(

            root,

            text="PLAYER STATISTICS",

            font=("Arial",20,"bold")

        )

        title.pack(pady=20)



        self.stats = tk.Label(

            root,

            font=("Arial",14),

            justify="left"

        )

        self.stats.pack(pady=20)



        self.refresh()



        button = tk.Button(

            root,

            text="Refresh Stats",

            command=self.refresh

        )

        button.pack(pady=10)



    def refresh(self):


        text = f"""

Player Name:
{self.player.name}


Games Played:
{self.player.games_played}


Wins:
{self.player.wins}


Losses:
{self.player.losses}


Win Rate:
{self.player.get_win_rate():.2f}%


Local Mode Wins:
{self.player.local_wins}


AI Mode Wins:
{self.player.ai_wins}


Total Spaces Captured:
{self.player.total_spaces}

        """


        self.stats.config(text=text)




# -------------------------
# GAME SYSTEM EXAMPLE
# -------------------------


player = PlayerStats("Player 1")



# Example:
# After player finishes a match,
# the game system calls this:


player.update_game(

    result="win",

    mode="ai",

    spaces=10

)


player.update_game(

    result="loss",

    mode="local",

    spaces=8

)




# Open stats screen

window = tk.Tk()


screen = StatsScreen(

    window,

    player

)


window.mainloop()
