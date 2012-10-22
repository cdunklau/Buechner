# Buechner

Upload your Flask static files to Amazon S3

## What's it do?

Buechner leverages [Boto](https://github.com/boto/boto) to let you easily push
static files to S3. It doesn't require Flask, that's just what I use it for.

Configuration is done by environment variables or by a file. This makes it easy
to use Buechner to throw static files at your S3 bucket through a git hook from
Heroku.

It will only transfer files that are newer than their counterparts on S3. It
won't delete anything, only overwrite.

## Usage

Drop buechner.py into your main project directory. It assumes your static
dir is at src/static relative to its own directory, but you can change that by
adding BUECHNER_STATIC_RELPATH to your environment. Note that this path is
defined with respect to Buechner's file path.

Set up your environment or a file 'aws_config.py' like so:

    AWS_S3_BUCKET = 'my_s3_bucket_name'
    AWS_ACCESS_KEY_ID = 'SPAM'
    AWS_SECRET_ACCESS_KEY = 'SECRETEGGS'

And then run `python buechner.py`. It will ask you to continue after confirming
the bucket name and static directory path.

## Requirements

*  [Boto](https://github.com/boto/boto)
*  Python 2.6 or above. Does not support Python 3.
*  Unix of some sort. The local file discovery might work on Windows, but I
   haven't tried.

## Etc

Create an issue or shoot me a pull request if you have the need.
