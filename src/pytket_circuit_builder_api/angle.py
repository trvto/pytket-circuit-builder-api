import sympy


class Angle:
    """Class for representing concrete or symbolic angles."""

    expr: sympy.Expr

    def __init__(self, ang: float | str) -> None:
        """Initialize from a float or a string."""
        self.expr = sympy.sympify(ang)
