from exporter import create_app
from exporter.config import Config

app = create_app(Config())

if __name__ == "__main__":
    app.run()
