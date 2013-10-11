/*
 *
 * Minimalistic Packet Sniffer
 * Written by: Michael Coppola
 * URL: http://www.poppopret.org/
 *
 * ./sniff 80 1337
 *
 */

#include <errno.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <netinet/ip.h>
#include <netinet/if_ether.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <unistd.h>

void process_packet(unsigned char *, int);
void print_tcp_packet(unsigned char *, int);
void print_data(unsigned char *, int);

struct sockaddr_in source, dest;
int target_port, listen_port;

void read_from_pipe ( int fd )
{
    int c;
    FILE *stream;

    stream = fdopen(fd, "r");
    while ( (c = fgetc(stream)) != EOF )
        putchar(c);
    fclose(stream);
}

int main ( int argc, char **argv )
{
    int saddr_size, data_size, sock_raw, result, mypipe[2];
    char *endptr;
    struct sockaddr saddr;

    target_port = strtol(argv[1], &endptr, 0);
    if ( *endptr )
    {
        printf("Invalid target port number.\n");
        return 1;
    }

    listen_port = strtol(argv[2], &endptr, 0);
    if ( *endptr )
    {
        printf("Invalid listen port number.\n");
        return 1;
    }

    unsigned char *buffer = (unsigned char *)malloc(65536);

    if ( pipe(mypipe) )
    {
        printf("Pipe creation failed.\n");
        exit(1);
    }

    if ( fork() == 0 )
    {
        sock_raw = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));

        if ( sock_raw < 0 )
        {
            printf("socket() error\n");
            return 1;
        }

        dup2(mypipe[1], 1);

        while ( 1 )
        {
            saddr_size = sizeof(saddr);
            memset(buffer, 0, sizeof(buffer));
            data_size = recvfrom(sock_raw, buffer, 65536, 0, &saddr, (socklen_t *)&saddr_size);
            if ( data_size < 0 )
            {
                printf("recvfrom() error, failed to get packets\n");
                return 1;
            }
            process_packet(buffer, data_size);
        }
    }
    else
    {
        int sockfd, result;
        struct sockaddr_in sin;

        if ( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0 )
        {
            printf("Error creating socket.\n");
            return;
        }

        memset(&sin, 0, sizeof(sin));
        sin.sin_family = AF_INET;
        sin.sin_addr.s_addr = htonl(INADDR_ANY);
        sin.sin_port = htons(listen_port);

        printf("Bound to port %d, waiting for connection...\n", listen_port);

        if ( bind(sockfd, (struct sockaddr *)&sin, sizeof(sin)) < 0 )
        {
            printf("Error binding to port.\n");
            return 1;
        }

        if ( listen(sockfd, 1) < 0 )
        {
            printf("Error listening for connections.\n");
            return 1;
        }

        while ( 1 )
        {
            if ( (result = accept(sockfd, NULL, 0)) < 0 )
            {
                printf("Error accepting new connection.\n");
                return 1;
            }

            printf("Received connection to monitor traffic.\n");

            if ( fork() == 0 )
            {
                dup2(result, 1);
                close(mypipe[1]);

                while ( 1 )
                    read_from_pipe(mypipe[0]);

                return 0;
            }
            else
                close(result);
        }
    }

    close(sock_raw);

    return 0;
}

void process_packet ( unsigned char *buffer, int size )
{
    struct iphdr *iph = (struct iphdr*)(buffer + sizeof(struct ethhdr));

    switch ( iph->protocol )
    {
        case 6: // tcp
            print_tcp_packet(buffer, size);
            break;

        default: // anything else
            break;
    }
}

void print_tcp_packet ( unsigned char *buffer, int size )
{
    unsigned short iphdrlen;

    struct iphdr *iph = (struct iphdr *)(buffer + sizeof(struct ethhdr));
    iphdrlen = iph->ihl*4;
    struct tcphdr *tcph = (struct tcphdr *)(buffer + iphdrlen + sizeof(struct ethhdr));
    int header_size = sizeof(struct ethhdr) + iphdrlen + tcph->doff*4;

    if ( (ntohs(tcph->dest) == target_port) )
    {
        struct iphdr *iph = (struct iphdr *)(buffer + sizeof(struct ethhdr));

        if ( size - header_size == 0 ) // Skip printing empty payloads
            return;

        // Usually memset() these structs to 0, but we're only using the src/dest addrs
        source.sin_addr.s_addr = iph->saddr;
        dest.sin_addr.s_addr = iph->daddr;

        printf("TCP packet:\n");
        printf("\tSource: %s:%u\n", inet_ntoa(source.sin_addr), ntohs(tcph->source));
        printf("\tDest: %s:%u\n", inet_ntoa(dest.sin_addr), ntohs(tcph->dest));
        printf("--- Payload ---\n");
        print_data(buffer + header_size, size - header_size);
        printf("\n===================================\n\n");
    }
}

void print_data ( unsigned char *data , int size )
{
    int i, j;
    for ( i = 0; i < size ; i++ )
    {
        if ( (i != 0) && (i % 16 == 0) )
        {
            printf("         ");
            for ( j = i - 16; j < i; j++ )
            {
                if ( data[j] >= 32 && data[j] <= 128 )
                    printf("%c", (unsigned char)data[j]);
                else
                    printf(".");
            }
            printf("\n");
        }

        if ( i % 16 == 0 )
            printf("   ");
        printf(" %02x", (unsigned int)data[i]);

        if ( i == size - 1 )
        {
            for ( j = 0; j < 15 - i % 16; j++ )
                printf("   ");

            printf("         ");

            for ( j = i - i % 16; j <= i; j++ )
            {
                if ( data[j] >= 32 && data[j] <= 128)
                    printf("%c",(unsigned char)data[j]);
                else
                    printf(".");
            }

            printf("\n");
        }
    }
}

