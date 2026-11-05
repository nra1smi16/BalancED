"""
Builds the numbers for the stress history chart (a plain SVG line chart).
Everything is calculated here so the template only has to place the shapes.
"""

WIDTH, HEIGHT = 640, 280
LEFT, RIGHT, TOP, BOTTOM = 48, 20, 16, 40

# (level, from score, to score); the same as predictor.level_for_score
LEVEL_BANDS = [('Normal', 0, 25), ('Mild', 25, 50), ('Moderate', 50, 75), ('High Risk', 75, 100)]


def _css(level):
    return level.lower().replace(' ', '-')


def _label(moment):
    try:
        from django.utils import timezone
        if timezone.is_aware(moment):
            moment = timezone.localtime(moment)
    except Exception:          # use the value as it is outside Django tests
        pass
    return f'{moment:%b} {moment.day}'


def build_chart(checkins):
    """checkins: assessments that have a score, OLDEST first."""
    plot_width = WIDTH - LEFT - RIGHT
    plot_height = HEIGHT - TOP - BOTTOM
    y_of = lambda score: TOP + (100 - score) / 100 * plot_height

    bands = [{'level': level, 'class': _css(level),
              'y': round(y_of(high), 1), 'height': round(y_of(low) - y_of(high), 1)}
             for level, low, high in LEVEL_BANDS]
    ticks = [{'value': value, 'y': round(y_of(value), 1)} for value in (0, 25, 50, 75, 100)]

    points = []
    if checkins:
        times = [c.created_at.timestamp() for c in checkins]
        first, last = min(times), max(times)
        for checkin, moment in zip(checkins, times):
            x = LEFT + (plot_width / 2 if last == first else (moment - first) / (last - first) * plot_width)
            points.append({'x': round(x, 1), 'y': round(y_of(checkin.stress_score), 1),
                           'score': round(checkin.stress_score), 'level': checkin.stress_level,
                           'class': _css(checkin.stress_level), 'label': _label(checkin.created_at)})

    if len(points) == 1:
        x_labels = [{'x': points[0]['x'], 'text': points[0]['label'], 'anchor': 'middle'}]
    elif points:
        x_labels = [{'x': LEFT, 'text': points[0]['label'], 'anchor': 'start'},
                    {'x': WIDTH - RIGHT, 'text': points[-1]['label'], 'anchor': 'end'}]
    else:
        x_labels = []

    return {
        'width': WIDTH, 'height': HEIGHT, 'left': LEFT, 'plot_width': plot_width,
        'tick_x': LEFT - 8, 'band_label_x': LEFT + 8, 'label_y': HEIGHT - 12,
        'bands': bands, 'ticks': ticks, 'points': points, 'x_labels': x_labels,
        'path': ' '.join(f"{p['x']},{p['y']}" for p in points), 'count': len(points),
    }
