import pytest
from app import app, db


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert "Système de Quiz" in response.data.decode('utf-8')

def test_submit(client):
    user_data = {
        'username': 'test_user',
        '1': '3',
        '2': '2',
        # Ajoutez d'autres réponses ici...
    }

    response = client.post('/submit', data=user_data, follow_redirects=True)
    assert response.status_code == 200
    assert "test_user" in response.data.decode('utf-8')  # Vérifie le nom d'utilisateur
    assert "<td>2</td>" in response.data.decode('utf-8')  # Vérifie le score



def test_scores(client):
    response = client.get('/scores')
    assert response.status_code == 200
    assert b"Tableau des Scores" in response.data
