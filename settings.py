import tkinter as tk


class SettingsScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.light_colors = ("#B8B8B8",)
        self.default_palette = ["#808080", "#F39C12", "#7CB342", "#3498DB", "#E74C3C"]

        self.title_label = tk.Label(self, text="Settings", font=("Arial", 30, "bold"))
        self.title_label.pack(pady=(35, 25))

        self.settings_row = tk.Frame(self)
        self.settings_row.pack(pady=20)

        self.section_label = tk.Label(self.settings_row, text="Theme Color", font=("Arial", 18, "bold"))
        self.section_label.pack(side="left", padx=(0, 20))

        # Keep track of the selected radio-button color.
        self.selected_color = tk.StringVar(value=controller.background_color)

        self.color_frame = tk.Frame(self.settings_row)
        self.color_frame.pack(side="left")

        # The middle option contains all five original page colors.
        color_choices = [
            ("#505050", ["#505050"]),
            ("default", self.default_palette),
            ("#B8B8B8", ["#B8B8B8"])
        ]

        for choice_value, square_colors in color_choices:
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
            color_option.pack(side="left", padx=10)
            # Keep the image available while this screen is open.
            color_option.image = square_image

        back_button = tk.Button(
            self,
            text="Back",
            command=lambda: controller.show_frame("MainMenu"),
            font=("Arial", 16, "bold"),
            width=12
        )
        back_button.pack(pady=30)

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

    def change_color(self):
        selected_choice = self.selected_color.get()
        self.apply_theme(selected_choice)
        # Save the chosen color so other screens can reuse it.
        self.controller.set_background_color(selected_choice)

    def on_show(self):
        self.selected_color.set(self.controller.background_color)
        self.apply_theme(self.controller.background_color)
