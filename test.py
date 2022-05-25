import sys

from main import Tracer, annotated_lines


def foo(x):
    d = x * 2
    return bar(d)


def bar(y):
    z = y + 1
    for i, i2 in zip(range(3), range(1, 4)):
        z += i + i2
    return z


def test_stuff():
    tracer = Tracer(__file__)
    tracer.set_trace()
    foo(3)
    sys.settrace(None)

    assert tracer.result == {
        "foo": {
            "source": {
                "lines": [
                    "def foo(x):\n",
                    "    d = x * 2\n",
                    "    return bar(d)\n"
                ],
                "startline": 6
            },
            "calls": [
                {
                    "args": {
                        "x": "3"
                    },
                    "lines": [
                        1,
                        2
                    ],
                    "assignments": {
                        1: [
                            {
                                "d": "6"
                            }
                        ]
                    },
                    "return": 16
                }
            ]
        },
        "bar": {
            "source": {
                "lines": [
                    "def bar(y):\n",
                    "    z = y + 1\n",
                    "    for i, i2 in zip(range(3), range(1, 4)):\n",
                    "        z += i + i2\n",
                    "    return z\n"
                ],
                "startline": 11
            },
            "calls": [
                {
                    "args": {
                        "y": "6"
                    },
                    "lines": [
                        1,
                        2,
                        3,
                        2,
                        3,
                        2,
                        3,
                        2,
                        4
                    ],
                    "assignments": {
                        1: [
                            {
                                "z": "7"
                            }
                        ],
                        2: [
                            {
                                "i": "0",
                                "i2": "1"
                            },
                            {
                                "i": "1",
                                "i2": "2"
                            },
                            {
                                "i": "2",
                                "i2": "3"
                            },
                            {
                                "i": "2",
                                "i2": "3"
                            }
                        ],
                        3: [
                            {
                                "z": "8"
                            },
                            {
                                "z": "11"
                            },
                            {
                                "z": "16"
                            }
                        ]
                    },
                    "return": 16
                }
            ]
        }
    }
    # print(json.dumps(tracer.result, indent=4))

    func_info = tracer.result["foo"]
    call = func_info["calls"][0]
    assert annotated_lines(func_info, call) == [
        'def foo(x):',
        '    d = x * 2  # d = 6',
        '    return bar(d)',
    ]

    func_info = tracer.result["bar"]
    call = func_info["calls"][0]
    assert annotated_lines(func_info, call) == [
        'def bar(y):',
        '    z = y + 1  # z = 7',
        '    for i, i2 in zip(range(3), range(1, 4)):  # i = 0, i2 = 1',
        '        z += i + i2  # z = 8',
        '    return z'
    ]
