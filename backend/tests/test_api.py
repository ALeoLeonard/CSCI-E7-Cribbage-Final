"""Integration tests for game REST API."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_new_game():
    resp = client.post("/api/v1/game/new", json={"player_name": "Alice"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "discard"
    assert data["player"]["name"] == "Alice"
    assert data["opponent"]["name"] == "Computer"
    assert len(data["player"]["hand"]) == 6
    assert data["opponent"]["hand_count"] == 4  # computer already discarded 2


def test_get_game():
    resp = client.post("/api/v1/game/new", json={})
    game_id = resp.json()["game_id"]
    resp2 = client.get(f"/api/v1/game/{game_id}")
    assert resp2.status_code == 200
    assert resp2.json()["game_id"] == game_id


def test_get_game_not_found():
    resp = client.get("/api/v1/game/nonexistent")
    assert resp.status_code == 404


def test_discard_cards():
    resp = client.post("/api/v1/game/new", json={})
    data = resp.json()
    game_id = data["game_id"]

    resp2 = client.post(
        f"/api/v1/game/{game_id}/discard",
        json={"card_indices": [0, 1]},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["phase"] == "play"
    assert len(data2["player"]["hand"]) == 4
    assert data2["starter"] is not None


def test_discard_invalid_count():
    resp = client.post("/api/v1/game/new", json={})
    game_id = resp.json()["game_id"]

    resp2 = client.post(
        f"/api/v1/game/{game_id}/discard",
        json={"card_indices": [0]},
    )
    assert resp2.status_code == 400


def test_full_game_flow():
    """Play through a complete round: discard → play all cards → count phases."""
    resp = client.post("/api/v1/game/new", json={"player_name": "Tester"})
    data = resp.json()
    game_id = data["game_id"]

    # Discard
    resp = client.post(f"/api/v1/game/{game_id}/discard", json={"card_indices": [0, 1]})
    data = resp.json()
    assert data["phase"] == "play"

    # Play all cards (or say go when can't)
    max_turns = 50
    for _ in range(max_turns):
        data = client.get(f"/api/v1/game/{game_id}").json()
        if data["phase"] != "play":
            break

        hand = data["player"]["hand"]
        running = data["running_total"]

        # Find a playable card
        played = False
        for i, card in enumerate(hand):
            if card["value"] + running <= 31:
                resp = client.post(
                    f"/api/v1/game/{game_id}/play",
                    json={"card_index": i},
                )
                assert resp.status_code == 200
                played = True
                break

        if not played:
            # Say go
            resp = client.post(f"/api/v1/game/{game_id}/go")
            assert resp.status_code == 200

    # Now we should be in a counting phase
    data = client.get(f"/api/v1/game/{game_id}").json()
    assert data["phase"] in ["count_non_dealer", "count_dealer", "count_crib", "game_over"]

    # Acknowledge through counting
    for _ in range(3):
        data = client.get(f"/api/v1/game/{game_id}").json()
        if data["phase"] == "game_over" or data["phase"] == "discard":
            break
        resp = client.post(f"/api/v1/game/{game_id}/acknowledge")
        assert resp.status_code == 200

    # Should be either in a new round (discard) or game over
    data = client.get(f"/api/v1/game/{game_id}").json()
    assert data["phase"] in ["discard", "game_over"]


def _play_one_round(game_id: str) -> dict:
    """Helper: play through one complete round (discard → play → count). Returns final state."""
    # Discard
    data = client.get(f"/api/v1/game/{game_id}").json()
    if data["phase"] != "discard":
        return data
    resp = client.post(f"/api/v1/game/{game_id}/discard", json={"card_indices": [0, 1]})
    assert resp.status_code == 200

    # Play all cards
    for _ in range(50):
        data = client.get(f"/api/v1/game/{game_id}").json()
        if data["phase"] != "play":
            break
        hand = data["player"]["hand"]
        running = data["running_total"]
        played = False
        for i, c in enumerate(hand):
            if c["value"] + running <= 31:
                resp = client.post(f"/api/v1/game/{game_id}/play", json={"card_index": i})
                assert resp.status_code == 200
                played = True
                break
        if not played:
            resp = client.post(f"/api/v1/game/{game_id}/go")
            assert resp.status_code == 200

    # Acknowledge through counting
    for _ in range(3):
        data = client.get(f"/api/v1/game/{game_id}").json()
        if data["phase"] in ("discard", "game_over"):
            break
        resp = client.post(f"/api/v1/game/{game_id}/acknowledge")
        assert resp.status_code == 200

    return client.get(f"/api/v1/game/{game_id}").json()


def test_multi_round_game_flow():
    """Play through multiple rounds to verify dealer rotation and round number."""
    resp = client.post("/api/v1/game/new", json={"player_name": "Tester"})
    game_id = resp.json()["game_id"]

    for expected_round in range(1, 4):
        data = client.get(f"/api/v1/game/{game_id}").json()
        if data["phase"] == "game_over":
            break
        assert data["round_number"] == expected_round
        data = _play_one_round(game_id)
        if data["phase"] == "game_over":
            break

    # Verify game is either still running or someone won
    data = client.get(f"/api/v1/game/{game_id}").json()
    assert data["phase"] in ["discard", "game_over"]
    if data["phase"] == "game_over":
        assert data["winner"] is not None


def test_his_heels_via_api():
    """If the starter is a Jack, the dealer should get 2 points."""
    # We can't guarantee this in a single game, but we can test
    # that the API handles the phase transition correctly regardless
    resp = client.post("/api/v1/game/new", json={"player_name": "Tester"})
    data = resp.json()
    game_id = data["game_id"]

    resp = client.post(f"/api/v1/game/{game_id}/discard", json={"card_indices": [0, 1]})
    data = resp.json()
    # After discard, should be in play or game_over (if His Heels won)
    assert data["phase"] in ["play", "game_over"]
    assert data["starter"] is not None
