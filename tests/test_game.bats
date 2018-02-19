#!/usr/bin/bats

load 'libs/bats-support/load'
load 'libs/bats-assert/load'


@test "scbw.play is installed" {
    command -v scbw.play
}

@test "ExampleBot loses against CherryPi" {
    TEST_DIR=/tmp/scbw_test

    # Delete lingering test dir
    [ -d $TEST_DIR ] && rm -rf $TEST_DIR

    mkdir $TEST_DIR $TEST_DIR/bots $TEST_DIR/maps $TEST_DIR/maps/replays $TEST_DIR/log $TEST_DIR/bwta $TEST_DIR/bwta2
    cp -r ExampleBot $TEST_DIR/bots
    cp -r CherryPi $TEST_DIR/bots
    cp maps/\(2\)Benzene.scx $TEST_DIR/maps

    run scbw.play \
        --bots ExampleBot CherryPi \
        --log_level=WARN \
        --game_speed=0 \
        --game_name="TEST" \
        --map="(2)Benzene.scx" \
        --bot_dir=$TEST_DIR/bots \
        --log_dir=$TEST_DIR/log \
        --map_dir=$TEST_DIR/maps \
        --bwapi_data_bwta2_dir=$TEST_DIR/bwta2 \
        --read_overwrite \
        --headless
    # check winner
    assert_output "1"

    # check logs
    run ls $TEST_DIR/log/GAME_TEST_0_ExampleBot_bot.log | wc -l
    assert_output "1"
    run ls $TEST_DIR/log/GAME_TEST_0_ExampleBot_game.log | wc -l
    assert_output "1"
    run ls $TEST_DIR/log/GAME_TEST_0_frames.csv | wc -l
    assert_output "1"
    run ls $TEST_DIR/log/GAME_TEST_0_results.json | wc -l
    assert_output "1"
    run ls $TEST_DIR/log/GAME_TEST_1_CherryPi_bot.log | wc -l
    assert_output "1"
    run ls $TEST_DIR/log/GAME_TEST_1_CherryPi_game.log | wc -l
    assert_output "1"
    run ls $TEST_DIR/log/GAME_TEST_1_frames.csv | wc -l
    assert_output "1"
    run ls $TEST_DIR/log/GAME_TEST_1_results.json | wc -l
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
    run ls $TEST_DIR/bots/CherryPi/write/GAME_TEST_1/openings_examplebot.json | wc -l
    assert_output "1"

    # check read folder has been updated
    run ls $TEST_DIR/bots/CherryPi/read/openings_examplebot.json | wc -l
    assert_output "1"

    # Clean up.
    rm -rf $TEST_DIR
}

