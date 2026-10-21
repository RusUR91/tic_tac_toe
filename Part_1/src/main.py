from di.container import container


def main():
    app = container.app
    app.run(debug=True, port=5000)


if __name__ == '__main__':
    main()