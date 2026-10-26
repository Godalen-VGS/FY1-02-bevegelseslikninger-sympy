"""Automatisk retting av FY1-02-bevegelseslikninger-sympy.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1a', 's_brems skal være ca. 52.1 m', 'naer(s_brems, 625/12, rel=1e-4)'),
    ('1b', 't_brems skal være ca. 4.17 s', 'naer(t_brems, 25/6, rel=1e-4)'),
    ('2a', 'h_maks skal være ca. 7.34 m', 'naer(h_maks, 144/(2*9.81), rel=1e-4)'),
    ('2b', 't_tilbake skal være ca. 2.45 s', 'naer(t_tilbake, 24/9.81, rel=1e-4)'),
    ('3', 't_uttrykk skal være de to løsningene av s = v0·t + at²/2 for t', "lik(t_uttrykk, [S('(-v0 - sqrt(v0**2 + 2*a*s))/a'), S('(-v0 + sqrt(v0**2 + 2*a*s))/a')])"),
    ('4_80', 'stopplengde(80, 1, 7) skal gi ca. 57.5 m', 'naer(stopplengde(80, 1, 7), 80/3.6 + (80/3.6)**2/14, rel=1e-4)'),
    ('4_50', 'stopplengde(50, 1.5, 8) skal gi ca. 32.9 m', 'naer(stopplengde(50, 1.5, 8), 50/3.6*1.5 + (50/3.6)**2/16, rel=1e-4)'),
    ('5', 't_innhenting skal være 20 s og s_innhenting 400 m', 'naer(t_innhenting, 20) and naer(s_innhenting, 400)'),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse
