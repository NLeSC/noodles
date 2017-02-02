Remote Dockerfile
=================

This Dockerfile builds an image running Python 3.5 with NumPy, SciPy and 
Noodles. This installation is then made accessible to the user through SSH
and SLURM. This image is currently based on debian testing. To create the 
Docker image::

    ../remote-docker> docker build -t noodles-remote .
    Sending build context to Docker daemon ...
    <<< Lots and lots of output >>>
    
Then start the service by::

    ../remote-docker> docker run -p 10022:22 -d noodles-remote
    <<< long hexadecimal number >>>
    
To ascertain that the Noodles server is indeed running, do::

    ../remote-docker> docker ps
    
That should show you that SSH is running with the correct port forwarding.
There are two ways to access the Docker container with SSH::

    ../remote-docker> ssh joe@0.0.0.0 -p 10022
    joe@0.0.0.0's password: <<< type the password: sixpack >>>

Or use the provided SHA key to allow non-password login for the user 'joe'::

    ../remote-docker> ssh -i ./id_rsa joe@0.0.0.0 -p 10022
    Welcome to the Noodles remote mockup!
    
    $

