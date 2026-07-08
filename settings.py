import tkinter as tk
from tkinter import simpledialog


class SettingsScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # ==================== START OF COLOR THEME CHANGES ====================
        self.light_colors = ("#B8B8B8",)
        self.default_palette = ["#808080", "#F39C12", "#7CB342", "#3498DB", "#E74C3C"]
        self.grey_palette = ["#303030", "#606060", "#909090", "#C0C0C0", "#E0E0E0"]
        # ===================== END OF COLOR THEME CHANGES =====================

        self.title_label = tk.Label(self, text="Settings", font=("Arial", 30, "bold"))
        self.title_label.pack(pady=(32, 12))

        # ==================== START OF ALIGNED SETTINGS ROW LAYOUT ====================
        self.settings_row = tk.Frame(self)
        self.settings_row.pack(pady=7)

        self.section_label = tk.Label(self.settings_row, text="Theme Color", font=("Arial", 18, "bold"))
        self.section_label.configure(width=20, anchor="e")
        self.section_label.grid(row=0, column=0, sticky="e", padx=(0, 35), pady=9)

        # Keep track of the selected radio-button color.
        self.selected_color = tk.StringVar(value=controller.background_color)

        self.color_frame = tk.Frame(self.settings_row)
        self.color_frame.grid(row=0, column=1, sticky="w", pady=9)

        # The middle option contains all five original page colors.
        # ==================== START OF COLOR THEME CHANGES ====================
        color_choices = [
            ("default", self.default_palette),
            ("#505050", self.grey_palette)
        ]

        # Match the width of the five tile-color choices below. The two theme
        # choices sit above the second and fourth tile-color positions.
        for column in range(5):
            self.color_frame.grid_columnconfigure(column, minsize=62)
        # ===================== END OF COLOR THEME CHANGES =====================

        for option_index, (choice_value, square_colors) in enumerate(color_choices):
            # Each colored square is also the clickable radio button.
            square_image = self._make_color_square(square_colors)
            color_option = tk.Radiobutton(
                self.color_frame,
                image=square_image,
                variable=self.selected_color,
                value=choice_value,
                command=self.change_color,
                indicatoron=False,
                bg="#B0B0B0",
                activebackground="#B0B0B0",
                selectcolor="#707070",
                relief="raised",
                bd=3,
                highlightthickness=0,
                padx=0,
                pady=0,
                cursor="hand2"
            )
            target_column = (1, 3)[option_index]
            color_option.grid(row=0, column=target_column, padx=10)
            # Keep the image available while this screen is open.
            color_option.image = square_image

        # ==================== START OF PLAYER TILE COLOR SETTING ====================
        tile_color_row = tk.Frame(self.settings_row)
        tile_color_row.grid(row=1, column=1, sticky="w", pady=9)

        self.player_tile_label = tk.Label(
            self.settings_row,
            text="Player Tile Color",
            font=("Arial", 18, "bold"),
            width=20,
            anchor="e",
        )
        self.player_tile_label.grid(row=1, column=0, sticky="e", padx=(0, 35), pady=9)

        self.selected_tile_color = tk.StringVar(value=controller.player_tile_color)
        tile_colors = ["#FF0000", "#ADD8E6", "#FFD700", "#000000", "#FFFFFF"]

        for color in tile_colors:
            square_image = self._make_color_square([color])
            tile_option = tk.Radiobutton(
                tile_color_row,
                image=square_image,
                variable=self.selected_tile_color,
                value=color,
                command=self.change_tile_color,
                indicatoron=False,
                bg="#B0B0B0",
                activebackground="#B0B0B0",
                selectcolor="#707070",
                relief="raised",
                bd=3,
                highlightthickness=0,
                padx=0,
                pady=0,
                cursor="hand2",
            )
            tile_option.pack(side="left", padx=10)
            tile_option.image = square_image

        self.tile_color_row = tile_color_row
        # ===================== END OF PLAYER TILE COLOR SETTING =====================

        # ==================== START OF OPPONENT TILE COLOR SETTING ====================
        opponent_color_row = tk.Frame(self.settings_row)
        opponent_color_row.grid(row=2, column=1, sticky="w", pady=9)

        self.opponent_tile_label = tk.Label(
            self.settings_row,
            text="Opponent Tile Color",
            font=("Arial", 18, "bold"),
            width=20,
            anchor="e",
        )
        self.opponent_tile_label.grid(row=2, column=0, sticky="e", padx=(0, 35), pady=9)

        self.selected_opponent_color = tk.StringVar(value=controller.opponent_tile_color)

        for color in tile_colors:
            square_image = self._make_color_square([color])
            opponent_option = tk.Radiobutton(
                opponent_color_row,
                image=square_image,
                variable=self.selected_opponent_color,
                value=color,
                command=self.change_opponent_color,
                indicatoron=False,
                bg="#B0B0B0",
                activebackground="#B0B0B0",
                selectcolor="#707070",
                relief="raised",
                bd=3,
                highlightthickness=0,
                padx=0,
                pady=0,
                cursor="hand2",
            )
            opponent_option.pack(side="left", padx=10)
            opponent_option.image = square_image

        self.opponent_color_row = opponent_color_row
        # ===================== END OF OPPONENT TILE COLOR SETTING =====================

        # ==================== START OF QUESTION TIMER SETTING ====================
        self.settings_separator = tk.Frame(self.settings_row, height=2, bg="#707070")
        self.settings_separator.grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(12, 10)
        )

        self.question_timer_label = tk.Label(
            self.settings_row,
            text="Question Timer",
            font=("Arial", 18, "bold"),
            width=20,
            anchor="e",
        )
        self.question_timer_label.grid(
            row=4, column=0, sticky="e", padx=(0, 35), pady=9
        )

        self.question_timer_scale = tk.Scale(
            self.settings_row,
            from_=5,
            to=60,
            orient="horizontal",
            length=300,
            resolution=1,
            showvalue=True,
            command=self.change_question_timer,
        )
        self.question_timer_scale.set(controller.question_timer)
        self.question_timer_scale.grid(row=4, column=1, sticky="w", pady=9)
        # ===================== END OF QUESTION TIMER SETTING =====================

        # ==================== START OF CPU SKIP SETTING ====================
        self.cpu_skips_label = tk.Label(
            self.settings_row,
            text="Skips",
            font=("Arial", 18, "bold"),
            width=20,
            anchor="e",
        )
        self.cpu_skips_label.grid(
            row=5, column=0, sticky="e", padx=(0, 35), pady=9
        )

        self.cpu_skips_scale = tk.Scale(
            self.settings_row,
            from_=0,
            to=10,
            orient="horizontal",
            length=300,
            resolution=1,
            showvalue=True,
            command=self.change_cpu_skips,
        )
        self.cpu_skips_scale.set(controller.cpu_skips)
        self.cpu_skips_scale.grid(row=5, column=1, sticky="w", pady=9)
        # ===================== END OF CPU SKIP SETTING =====================

        # ==================== START OF GAME SETTINGS ====================
        self.set_mode_label = tk.Label(
            self.settings_row,
            text="Set Mode",
            font=("Arial", 18, "bold"),
            width=20,
            anchor="e",
        )
        self.set_mode_label.grid(
            row=6, column=0, sticky="e", padx=(0, 35), pady=9
        )

        self.set_mode_frame = tk.Frame(self.settings_row)
        self.set_mode_frame.grid(row=6, column=1, sticky="w", pady=9)
        self.selected_chance_mode = tk.StringVar(value=controller.cpu_chance_mode)

        mode_choices = [
            ("safe", "#2ECC71"),
            ("normal", "#F39C12"),
            ("chaos", "#E74C3C"),
        ]
        for mode, color in mode_choices:
            square_image = self._make_color_square([color])
            mode_option = tk.Radiobutton(
                self.set_mode_frame,
                image=square_image,
                variable=self.selected_chance_mode,
                value=mode,
                command=self.change_chance_mode,
                indicatoron=False,
                bg="#B0B0B0",
                activebackground="#B0B0B0",
                selectcolor="#707070",
                relief="raised",
                bd=3,
                highlightthickness=0,
                padx=0,
                pady=0,
                cursor="hand2",
            )
            mode_option.pack(side="left", padx=10)
            mode_option.image = square_image
        # ===================== END OF GAME SETTINGS =====================

        # ==================== START OF CHANGE NAME SETTING ====================
        self.name_separator = tk.Frame(self.settings_row, height=2, bg="#707070")
        self.name_separator.grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(12, 10)
        )

        self.change_name_button = tk.Button(
            self.settings_row,
            text="Change Name",
            command=self.change_name,
            font=("Arial", 15, "bold"),
            width=16,
        )
        self.change_name_button.grid(row=8, column=0, columnspan=2, pady=(5, 7))

        self.current_name_label = tk.Label(
            self.settings_row,
            text=controller.player_stats.name,
            font=("Arial", 14),
            width=28,
            bg="white",
            fg="black",
            relief="sunken",
            bd=2,
            padx=8,
            pady=6,
        )
        self.current_name_label.grid(row=9, column=0, columnspan=2, pady=(0, 6))
        # ===================== END OF CHANGE NAME SETTING =====================
        # ===================== END OF ALIGNED SETTINGS ROW LAYOUT =====================

        back_button = tk.Button(
            self,
            text="Back",
            command=lambda: controller.show_frame("MainMenu"),
            font=("Arial", 16, "bold"),
            width=12
        )
        back_button.pack(pady=12)

        self.apply_theme(controller.background_color)

    def _make_color_square(self, colors):
        """Create a small square containing one or more color stripes."""
        image = tk.PhotoImage(width=36, height=28)
        stripe_width = 36 // len(colors)

        for index, color in enumerate(colors):
            start = index * stripe_width
            end = 36 if index == len(colors) - 1 else start + stripe_width
            image.put(color, to=(start, 0, end, 28))

        return image

    def apply_theme(self, background_choice):
        page_color = "#E74C3C" if background_choice == "default" else background_choice
        text_color = "black" if page_color in self.light_colors else "white"

        self.configure(bg=page_color)
        self.title_label.configure(bg=page_color, fg=text_color)
        self.settings_row.configure(bg=page_color)
        self.section_label.configure(bg=page_color, fg=text_color)
        self.color_frame.configure(bg=page_color)
        self.player_tile_label.configure(bg=page_color, fg=text_color)
        self.tile_color_row.configure(bg=page_color)
        self.opponent_tile_label.configure(bg=page_color, fg=text_color)
        self.opponent_color_row.configure(bg=page_color)
        # ==================== START OF QUESTION TIMER SETTING ====================
        self.question_timer_label.configure(bg=page_color, fg=text_color)
        self.question_timer_scale.configure(bg=page_color, fg=text_color)
        # ===================== END OF QUESTION TIMER SETTING =====================
        # ==================== START OF CPU SKIP SETTING ====================
        self.cpu_skips_label.configure(bg=page_color, fg=text_color)
        self.cpu_skips_scale.configure(bg=page_color, fg=text_color)
        # ===================== END OF CPU SKIP SETTING =====================
        # ==================== START OF GAME SETTINGS ====================
        self.set_mode_label.configure(bg=page_color, fg=text_color)
        self.set_mode_frame.configure(bg=page_color)
        # ===================== END OF GAME SETTINGS =====================

    def change_color(self):
        selected_choice = self.selected_color.get()
        self.apply_theme(selected_choice)
        # Save the chosen color so other screens can reuse it.
        self.controller.set_background_color(selected_choice)

    # ==================== START OF TILE COLOR CHANGE METHODS ====================
    def change_tile_color(self):
        if not self.controller.set_player_tile_color(self.selected_tile_color.get()):
            self.selected_tile_color.set(self.controller.player_tile_color)

    def change_opponent_color(self):
        if not self.controller.set_opponent_tile_color(self.selected_opponent_color.get()):
            self.selected_opponent_color.set(self.controller.opponent_tile_color)
    # ===================== END OF TILE COLOR CHANGE METHODS =====================

    # ==================== START OF QUESTION TIMER SETTING ====================
    def change_question_timer(self, value):
        self.controller.set_question_timer(value)
    # ===================== END OF QUESTION TIMER SETTING =====================

    # ==================== START OF CPU SKIP SETTING ====================
    def change_cpu_skips(self, value):
        self.controller.set_cpu_skips(value)
    # ===================== END OF CPU SKIP SETTING =====================

    # ==================== START OF GAME SETTINGS ====================
    def change_chance_mode(self):
        self.controller.set_cpu_chance_mode(self.selected_chance_mode.get())
    # ===================== END OF GAME SETTINGS =====================

    # ==================== START OF CHANGE NAME SETTING ====================
    def change_name(self):
        new_name = simpledialog.askstring(
            "Change Name",
            "Enter your new name:",
            initialvalue=self.controller.player_stats.name,
            parent=self.controller,
        )
        if new_name and new_name.strip():
            self.controller.player_stats.name = new_name.strip()
            self.current_name_label.configure(text=self.controller.player_stats.name)
    # ===================== END OF CHANGE NAME SETTING =====================

    def on_show(self):
        self.selected_color.set(self.controller.background_color)
        # ==================== START OF TILE COLOR SETTINGS ====================
        self.selected_tile_color.set(self.controller.player_tile_color)
        self.selected_opponent_color.set(self.controller.opponent_tile_color)
        # ===================== END OF TILE COLOR SETTINGS =====================
        # ==================== START OF QUESTION TIMER SETTING ====================
        self.question_timer_scale.set(self.controller.question_timer)
        # ===================== END OF QUESTION TIMER SETTING =====================
        # ==================== START OF CPU SKIP SETTING ====================
        self.cpu_skips_scale.set(self.controller.cpu_skips)
        # ===================== END OF CPU SKIP SETTING =====================
        # ==================== START OF GAME SETTINGS ====================
        self.selected_chance_mode.set(self.controller.cpu_chance_mode)
        # ===================== END OF GAME SETTINGS =====================
        # ==================== START OF CHANGE NAME SETTING ====================
        self.current_name_label.configure(text=self.controller.player_stats.name)
        # ===================== END OF CHANGE NAME SETTING =====================
        self.apply_theme(self.controller.background_color)
