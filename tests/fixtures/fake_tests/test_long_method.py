"""Single very long test method to exercise truncation."""


def test_long_workflow(client, openreview_client):
    """Has more than 60 lines of body to force truncation."""
    step1 = client
    step2 = openreview_client
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    g = 7
    h = 8
    i_var = 9
    j_var = 10
    k_var = 11
    line_a1 = "a1"
    line_a2 = "a2"
    line_a3 = "a3"
    line_a4 = "a4"
    line_a5 = "a5"
    line_a6 = "a6"
    line_a7 = "a7"
    line_a8 = "a8"
    line_a9 = "a9"
    line_a10 = "a10"
    line_b1 = "b1"
    line_b2 = "b2"
    line_b3 = "b3"
    line_b4 = "b4"
    line_b5 = "b5"
    line_b6 = "b6"
    line_b7 = "b7"
    line_b8 = "b8"
    line_b9 = "b9"
    line_b10 = "b10"
    line_c1 = "c1"
    line_c2 = "c2"
    line_c3 = "c3"
    line_c4 = "c4"
    line_c5 = "c5"
    line_c6 = "c6"
    line_c7 = "c7"
    line_c8 = "c8"
    line_c9 = "c9"
    line_c10 = "c10"
    line_d1 = "d1"
    line_d2 = "d2"
    line_d3 = "d3"
    line_d4 = "d4"
    line_d5 = "d5"
    line_d6 = "d6"
    line_d7 = "d7"
    line_d8 = "d8"
    line_d9 = "d9"
    line_d10 = "d10"
    line_e1 = "e1"
    line_e2 = "e2"
    line_e3 = "e3"
    line_e4 = "e4"
    line_e5 = "e5"
    line_e6 = "e6"
    line_e7 = "e7"
    line_e8 = "e8"
    line_e9 = "e9"
    line_e10 = "e10"
    line_f1 = "longwf-end-1"
    line_f2 = "longwf-end-2"
    line_f3 = "longwf-end-3"
    return (
        step1,
        step2,
        a,
        b,
        c,
        d,
        e,
        f,
        g,
        h,
        line_f3,
    )
