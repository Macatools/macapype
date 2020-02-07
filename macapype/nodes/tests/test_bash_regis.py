from macapype.nodes.bash_regis import T1xT2BET

def test_T1xT2BET():

    bet = T1xT2BET()
    print(bet.cmdline)

    bet.run()

