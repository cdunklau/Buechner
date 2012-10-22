#!/usr/bin/env python
import os
import sys
from datetime import datetime

from boto.s3.connection import S3Connection
from boto.s3.key import Key

# Relative path from directory of buechner.py. Default to src/static,
# but script will attempt to pull from BUECHNER_STATIC_RELPATH env var.
try:
    STATIC_DIR_REL = os.environ['BUECHNER_STATIC_RELPATH']
except KeyError:
    STATIC_DIR_REL = os.path.join(
        'src',
        'static')


def init_s3_interface(s3_bucket, access_key_id, secret_access_key):
    """
    Initialize the interface.

    Arguments are all strings: bucket name, key id, and secret key,
    respectively. Returns a list of boto.s3.connection.S3Connection,
    boto.s3.bucket.Bucket.

    """
    conn = S3Connection(access_key_id, secret_access_key)
    bucket = conn.get_bucket(s3_bucket)
    return conn, bucket


def get_keys_from_directory(basedir):
    """
    Return dict of paths -> mtimes of files found recursively under `basedir`.

    Paths are relative to `basedir` with no leading slashes. Mtimes are
    datetime.datetime objects in UTC. Will not follow directory symlinks.

    Note: this will probably only work right on Unix, unless os.path.getmtime
    gives UTC on other platforms too.

    """
    results = []
    # Fill up results with base, namelist
    os.path.walk(
        basedir,
        (lambda x, y, z: results.append([y,z])),
        None)
    files = dict()
    for base, names in results:
        for name in names:
            fullpath = os.path.join(base, name)
            # only care about files
            if os.path.isfile(fullpath):
                mtime = datetime.utcfromtimestamp(os.path.getmtime(fullpath))
                relative_path = fullpath.replace(
                    basedir, '').lstrip(os.path.sep)
                files[relative_path] = mtime
    return files


def upload_new_files(staticdir, bucket):
    """
    Upload newer files recursively under `staticdir` to `bucket`.

    This assumes that the directory `staticdir` represents the root of
    the S3 bucket. `bucket` should be an instance of boto.s3.bucket.Bucket.

    Return a list of the files uploaded, with paths relative to `staticdir`.

    """
    allkeys = bucket.list()
    local_files_mtimes = get_keys_from_directory(staticdir)
    # `fmt` should be ISO 8601, but the time zone isn't parsed right when
    # given as %Z, so we hack it off below. Hopefully it's always Zulu time
    fmt = '%Y-%m-%dT%H:%M:%S.%f'
    # This is a dict of key_name -> [key_obj, key.last_modified]
    remote_files_mtimes_keys = dict(
        (
            k.name,
            [
                k,
                datetime.strptime(
                    k.last_modified[:-1],  # strip off Z at end
                    fmt)
            ]
        ) for k in allkeys)
    uploaded_files = []
    for filepath, local_mtime in local_files_mtimes.iteritems():
        if filepath in remote_files_mtimes_keys:
            the_key, remote_mtime = remote_files_mtimes_keys[filepath]
            # Skip file if local is older
            if remote_mtime > local_mtime:
                continue
        else:
            the_key = Key(bucket)
            the_key.key = filepath

        uploaded_files.append(filepath)
        the_key.set_contents_from_filename(os.path.join(staticdir, filepath))
    return uploaded_files


if __name__ == '__main__':
    # If no AWS keys are found in environment, try to import the config file
    try:
        AWS_S3_BUCKET = os.environ['AWS_S3_BUCKET']
        AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
        AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
        print "Using environment config. Loading bucket '%s'" % (
            AWS_S3_BUCKET)
    except KeyError:
        print (
            'Failed to find all environment variables, attempting to load '
            'aws_config.py...')
        try:
            import aws_config
            AWS_S3_BUCKET = aws_config.AWS_S3_BUCKET
            AWS_ACCESS_KEY_ID = aws_config.AWS_ACCESS_KEY_ID
            AWS_SECRET_ACCESS_KEY = aws_config.AWS_SECRET_ACCESS_KEY
            print "Using aws_config.py config. Loading bucket '%s'" % (
                AWS_S3_BUCKET)
        except (ImportError, NameError, AttributeError) as e:
            print 'Failed to locate AWS config, check environment or config'
            print "Error was: '%s'" % e
            sys.exit(1)

    staticdir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        STATIC_DIR_REL)
    print "Will upload new files from '%s' to bucket '%s'." % (
        staticdir,
        AWS_S3_BUCKET)
    if raw_input('Continue? [Y]').strip().lower() != 'y':
        print "Exiting..."
        sys.exit(1)
    print "Preparing upload..."
    conn, bucket = init_s3_interface(
        AWS_S3_BUCKET,
        AWS_ACCESS_KEY_ID,
        AWS_SECRET_ACCESS_KEY)
    uploaded = upload_new_files(staticdir, bucket)
    for filename in uploaded:
        print "Uploaded '%s' to S3" % filename
