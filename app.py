# Author Matthew Taylor

from flask import Flask, render_template
from flask_sock import Sock
from simple_websocket import ConnectionClosed
from Box2D import b2World, b2Vec2, b2EdgeShape, b2FixtureDef, b2CircleShape
import json
import random
import pygame

app = Flask(__name__)
sock = Sock(app)

WIDTH, HEIGHT = 800, 1000
world = b2World(gravity=(0, 0), doSleep=True)

player_body = world.CreateDynamicBody(
    position=(WIDTH / 2 / 10, 5),
    shapes=b2CircleShape(radius=2),
    linearDamping=0.5,
    angularDamping=0.5
)

balls = []
for _ in range(10):
    x = random.randint(100, WIDTH - 100) / 10
    y = random.randint(400, HEIGHT - 100) / 10
    body = world.CreateDynamicBody(position=(x, y), linearDamping=0.2, angularDamping=0.2)
    shape = body.CreateCircleFixture(radius=2, density=0.02, friction=0.2)
    balls.append((body, shape))

wall_top = world.CreateStaticBody(
    position=(0, HEIGHT / 10),
    fixtures=b2FixtureDef(
        shape=b2EdgeShape(vertices=[(0, 0), (WIDTH / 10, 0)]),
        restitution=1.0
    )
)

wall_bottom = world.CreateStaticBody(
    position=(0, 0),
    fixtures=b2FixtureDef(
        shape=b2EdgeShape(vertices=[(0, 0), (WIDTH / 10, 0)]),
        restitution=1.0
    )
)

wall_left = world.CreateStaticBody(
    position=(0, 0),
    fixtures=b2FixtureDef(
        shape=b2EdgeShape(vertices=[(0, 0), (0, HEIGHT / 10)]),
        restitution=1.0
    )
)

wall_right = world.CreateStaticBody(
    position=(WIDTH / 10, 0),
    fixtures=b2FixtureDef(
        shape=b2EdgeShape(vertices=[(0, 0), (0, HEIGHT / 10)]),
        restitution=1.0
    )
)

pygame.init()
clock = pygame.time.Clock()


@app.route('/', methods=['GET',"POST"])
def home():
    return render_template("index.html")

@sock.route('/echo')
def echo(connection):
    print('Client connected', connection)

    while True:
        world.Step(1/30, 5, 2)
        clock.tick(60)

        try:
            # send the world data to the clients
            player_position = player_body.transform * player_body.fixtures[0].shape.pos * 10
            player_data = {
                'x': player_position.x,
                'y': player_position.y,
                'id': 0
            }

            balls_data= []

            for i, (body, shape) in enumerate(balls):
                position = body.transform * shape.shape.pos * 10
                balls_data.append({'x': int(position[0]), 'y': int(position[1]), 'id': i})

            message = {'player': player_data, 'balls': balls_data}

            connection.send(json.dumps(message))
        except (ConnectionClosed, ConnectionError):
            print('Connection closed')
            break


@sock.route('/input')
def input(connection):
    while True:
        try:
            message = connection.receive()
            #print(message)
            data = json.loads(message)
            player_body.ApplyLinearImpulse(b2Vec2(data['x'], data['y']), player_body.worldCenter, True)
        except Exception as e:
            print(e)
            break


if __name__ == "__main__":
    app.run(debug=True)


