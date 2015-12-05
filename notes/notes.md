# psycopg2 / OS X

To make psycopg2 use OpenSSL 1.0.0:

    export DYLD_LIBRARY_PATH=/usr/local/Cellar/openssl/1.0.1c/lib

# Python

To stop Python output from being buffered:

1. Use the -u command line switch
2. Wrap sys.stdout in an object that flushes after every write
3. Set PYTHONUNBUFFERED env var
4. sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

See:

* [http://stackoverflow.com/questions/107705/python-output-buffering]
* [http://algorithmicallyrandom.blogspot.fr/2009/10/python-tips-and-tricks-flushing-stdout.html]
* [http://stackoverflow.com/questions/107705/python-output-buffering]

# Memcached
 
Assuming it's installed using Homebrew:

To have launchd start memcached at login:

    ln -sfv /usr/local/opt/memcached/*.plist ~/Library/LaunchAgents

Then to load memcached now:

    launchctl load ~/Library/LaunchAgents/homebrew.mxcl.memcached.plist

Or, if you don't want/need launchctl, you can just run:

    /usr/local/opt/memcached/bin/memcached

Add -d to daemonize.

# Gunicorn

To get more debug output out of Gunicorn:

    --debug --log-level debug

# Git

To view a deleted file in git:

    git show $(git rev-list --max-count=1 --all -- { filename })^:{ filename }
