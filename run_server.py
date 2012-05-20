import sys
from application import create_app, run_app

if __name__ == "__main__":
    if len(sys.argv) > 1:
        create_app(sys.argv[1])
        run_app()
    else:
        print "Usage: run_server run_mode"
        print "run_mode can be:"
        print "        dev - local, personal development server"
        print "       team - still local server, for development by team (specifically non-coder team members)"
        print " production - deployed on Heroku"
        sys.exit(1)
