import tkinter as tk


def run(window, show_menu, background_color, set_background_color):
    for widget in window.winfo_children():
        widget.destroy()

    # Settings uses red when the default palette is selected.
    page_color = "#E74C3C" if background_color == "default" else background_color
    light_colors = ("#B8B8B8",)
    text_color = "black" if page_color in light_colors else "white"
    window.configure(bg=page_color)

    title_label = tk.Label(
        window,
        text="Settings",
        font=("Arial", 30, "bold"),
        bg=page_color,
        fg=text_color
    )
    title_label.pack(pady=(35, 25))

    settings_row = tk.Frame(window, bg=page_color)
    settings_row.pack(pady=20)

    section_label = tk.Label(
        settings_row,
        text="Theme Color",
        font=("Arial", 18, "bold"),
        bg=page_color,
        fg=text_color
    )
    section_label.pack(side="left", padx=(0, 20))

    # Keep track of the selected radio-button color.
    selected_color = tk.StringVar(value=background_color)

    color_frame = tk.Frame(settings_row, bg=page_color)
    color_frame.pack(side="left")

    # The middle option contains all five original page colors.
    default_palette = ["#808080", "#F39C12", "#7CB342", "#3498DB", "#E74C3C"]
    color_choices = [
        ("#505050", ["#505050"]),
        ("default", default_palette),
        ("#B8B8B8", ["#B8B8B8"])
    ]

    def make_color_square(colors):
        """Create a small square containing one or more color stripes."""
        image = tk.PhotoImage(width=36, height=28)
        stripe_width = 36 // len(colors)

        for index, color in enumerate(colors):
            start = index * stripe_width
            end = 36 if index == len(colors) - 1 else start + stripe_width
            image.put(color, to=(start, 0, end, 28))

        return image

    def change_color():
        selected_choice = selected_color.get()
        new_color = "#E74C3C" if selected_choice == "default" else selected_choice
        text_color = "black" if new_color in light_colors else "white"

        # Update this screen and save the color for the main menu.
        window.configure(bg=new_color)
        title_label.configure(bg=new_color, fg=text_color)
        settings_row.configure(bg=new_color)
        section_label.configure(bg=new_color, fg=text_color)
        color_frame.configure(bg=new_color)
        set_background_color(selected_choice)

    for choice_value, square_colors in color_choices:
        # Each colored square is also the clickable radio button.
        square_image = make_color_square(square_colors)
        color_option = tk.Radiobutton(
            color_frame,
            image=square_image,
            variable=selected_color,
            value=choice_value,
            command=change_color,
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
        window,
        text="Back",
        command=show_menu,
        font=("Arial", 16, "bold"),
        width=12
    )
    back_button.pack(pady=30)
