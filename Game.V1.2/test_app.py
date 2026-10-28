import unittest
from unittest.mock import patch
import app as game_app

class GuessworkRoutesTest(unittest.TestCase):
    def setUp(self):
        game_app.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = game_app.app.test_client()

    def start(self, difficulty="easy", number=7):
        with patch("app.random.randint", return_value=number):
            return self.client.post("/", data={"difficulty": difficulty}, follow_redirects=True)

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"GUESSWORK", response.data)

    def test_all_difficulty_buttons_start_game(self):
        for difficulty, maximum in [("easy", 10), ("medium", 50), ("hard", 100), ("hardest", 1000)]:
            with self.subTest(difficulty=difficulty):
                response = self.start(difficulty, min(7, maximum))
                self.assertEqual(response.status_code, 200)
                self.assertIn(difficulty.encode(), response.data)

    def test_invalid_difficulty_is_handled(self):
        response = self.client.post("/", data={"difficulty": "impossible"})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Choose a valid difficulty", response.data)

    def test_guess_too_low_and_too_high(self):
        self.start("easy", 7)
        low = self.client.post("/guess", data={"guess": "3"}, follow_redirects=True)
        self.assertEqual(low.status_code, 200)
        self.assertIn(b"Too low", low.data)
        high = self.client.post("/guess", data={"guess": "9"}, follow_redirects=True)
        self.assertEqual(high.status_code, 200)
        self.assertIn(b"Too high", high.data)

    def test_invalid_guess_does_not_consume_attempt(self):
        self.start("easy", 7)
        response = self.client.post("/guess", data={"guess": "999"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["game"]["attempts"], 0)
        response = self.client.post("/guess", data={"guess": "1.5"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["game"]["attempts"], 0)

    def test_correct_guess_sets_best(self):
        self.start("easy", 7)
        response = self.client.post("/guess", data={"guess": "7"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"You found it", response.data)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["best"], 1)
            self.assertEqual(sess["game"]["status"], "won")

    def test_game_over_at_attempt_limit(self):
        self.start("easy", 7)
        self.client.post("/guess", data={"guess": "1"})
        response = self.client.post("/guess", data={"guess": "2"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ROUND OVER", response.data)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["game"]["status"], "lost")
            self.assertEqual(sess["game"]["attempts"], 2)

    def test_restart_get_and_post_work(self):
        self.start("easy", 7)
        for method in ("get", "post"):
            response = getattr(self.client, method)("/restart", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            with self.client.session_transaction() as sess:
                self.assertNotIn("game", sess)

    def test_guess_without_active_game_is_safe(self):
        response = self.client.post("/guess", data={"guess": "3"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_not_found_has_custom_page(self):
        response = self.client.get("/this-page-does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"SIGNAL NOT FOUND", response.data)

if __name__ == "__main__":
    unittest.main(verbosity=2)
