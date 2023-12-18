import sys
from lunchtag import app
import argparse

def get_port():
    """
    Uses argparse to get port number from command line arguments
    Returns the port in integer form.
    """
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        description="The YUAG search application"
    )
    parser.add_argument(
        'port',
        help="the port at which the server should listen"
    )
    arg = parser.parse_args()
    port = arg.port
    try:
        port = int(port)
        if not 0 <= int(port) <= 65536:
            print("Your port must be a valid number.")
            sys.exit(1)
    except ValueError:
        print("Your port must be numeric.")
        sys.exit(1)

    return port

def main():
    """Main function"""
    port = get_port()
    print(port)

    try:
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
