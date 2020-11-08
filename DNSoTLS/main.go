package main

import (
	"bufio"
	"crypto/tls"
	"encoding/binary"
	"log"
	"net"
	"os"
	"time"
)

func err(e error) bool {
	if e != nil {
		log.Print(e)
		return true
	}
	return false
}

func main() {
	cert, or := tls.LoadX509KeyPair("/etc/letsencrypt/live/dns.10x.es/fullchain.pem", "/etc/letsencrypt/live/dns.10x.es/privkey.pem")
	if err(or) {
		os.Exit(1)
	}
	cfg := &tls.Config{Certificates: []tls.Certificate{cert}}
	listen, or := tls.Listen("tcp4", "0.0.0.0:853", cfg)
	if err(or) {
		os.Exit(1)
	}
	log.Printf("Listening on %s", listen.Addr())
	for {
		conn, or := listen.Accept()
		if or != nil {
			log.Println(or)
			continue
		}
		go handle(conn)
	}
}

func handle(conn net.Conn) {
	var (
		buf = make([]byte, 1222)
		r   = bufio.NewReaderSize(conn, 310)
	)

	defer func() {
		recover()
		log.Printf("Client from %s disconnected", conn.RemoteAddr())
	}()
	defer func() {
		conn.Close()
	}()

	conn.SetDeadline(time.Now().Add(time.Duration(15) * time.Second))

	for {
		len, or := r.Read(buf)
		if or != nil || len > 1220 {
			return
		}

		dns, err := net.Dial("udp", "127.0.0.1:53")
		dns.SetDeadline(time.Now().Add(time.Duration(2) * time.Second))
		dns.Write(buf[2:len])

		rx := make([]byte, 1220)
		len, err = bufio.NewReader(dns).Read(rx)

		if err != nil {
			log.Println(err)
			return
		}
		lrx := make([]byte, 2)
		binary.BigEndian.PutUint16(lrx, uint16(len))

		conn.Write(append(lrx, rx[:len]...))
	}
}
