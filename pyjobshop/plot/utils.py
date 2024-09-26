import matplotlib


def get_colors() -> list[str]:
    """
    Color sequence based on concatenation of different common color maps.
    """
    names = ["tab20c", "Dark2", "Set1", "tab20b", "Set2", "tab20", "Accent"]
    cmaps = [matplotlib.colormaps[name] for name in names]
    colors = [color for cmap in cmaps for color in cmap.colors]

    return list(dict.fromkeys(colors))  # unique colors
