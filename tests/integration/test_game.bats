#!/usr/bin/bats

load 'libs/bats-support/load'
load 'libs/bats-assert/load'


@test "scbw.play is installed" {
    command -v scbw.play
}

@test "ExampleBot loses against ZZZKBot" {
    TEST_DIR=/tmp/scbw_test

    # Delete lingering test dir
    [ -d $TEST_DIR ] && rm -rf $TEST_DIR

    mkdir $TEST_DIR $TEST_DIR/bots $TEST_DIR/maps $TEST_DIR/maps/replays $TEST_DIR/games $TEST_DIR/bwta $TEST_DIR/bwta2
    cp -r ExampleBot $TEST_DIR/bots
    cp -r ZZZKBot $TEST_DIR/bots
    cp maps/\(2\)Benzene.scx $TEST_DIR/maps

    run scbw.play \
        --bots ExampleBot ZZZKBot \
        --log_level=WARN \
        --game_speed=0 \
        --game_name="TEST" \
        --map="(2)Benzene.scx" \
        --bot_dir=$TEST_DIR/bots \
        --game_dir=$TEST_DIR/games \
        --map_dir=$TEST_DIR/maps \
        --bwapi_data_bwta2_dir=$TEST_DIR/bwta2 \
        --docker_image=starcraft:game \
        --read_overwrite \
        --headless
    # check winner
    assert_output "1"

    # check logs
    run ls $TEST_DIR/games/GAME_TEST/log_0/bot.log | wc -l
    assert_output "1"
    run ls $TEST_DIR/games/GAME_TEST/log_0/game.log | wc -l
    assert_output "1"
    run ls $TEST_DIR/games/GAME_TEST/log_0/frames.csv | wc -l
    assert_output "1"
    run ls $TEST_DIR/games/GAME_TEST/log_0/results.json | wc -l
    assert_output "1"
    run ls $TEST_DIR/games/GAME_TEST/log_1/bot.log | wc -l
    assert_output "1"
    run ls $TEST_DIR/games/GAME_TEST/log_1/game.log | wc -l
    assert_output "1"
    run ls $TEST_DIR/games/GAME_TEST/log_1/frames.csv | wc -l
    assert_output "1"
    run ls $TEST_DIR/games/GAME_TEST/log_1/results.json | wc -l
    assert_output "1"

    # check replays
    run ls $TEST_DIR/maps/replays/GAME_TEST_0.rep | wc -l
    assert_output "1"
    run ls $TEST_DIR/maps/replays/GAME_TEST_1.rep | wc -l
    assert_output "1"

    # check BWTA2
    run ls $TEST_DIR/bwta2/*bwta | wc -l
    assert_output "1"

    # check write folder has contents
    run ls $TEST_DIR/games/GAME_TEST/write_1/ZZZKBot_v_1.5.0.0.0_Zerg_vs_ExampleBot_Terran.dat | wc -l
    assert_output "1"

    # check read folder has been updated
    run ls $TEST_DIR/bots/ZZZKBot/read/ZZZKBot_v_1.5.0.0.0_Zerg_vs_ExampleBot_Terran.dat | wc -l
    assert_output "1"

    # Clean up.
    rm -rf $TEST_DIR
}

