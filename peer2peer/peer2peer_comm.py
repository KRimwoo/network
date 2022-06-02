#20190068 Woorim Kim HW3.py

import sys
import socket
import select


tcpPort = sys.argv[1]
userId = sys.argv[2]
userName = sys.argv[3]
userSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
userSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
userSocket.bind(('', int(tcpPort)))
userSocket.listen()
connectionSocket = [userSocket , sys.stdin]
querySeq = 0
queries = []
q_forme = []
running = 1
while running:
    print(f"{userId}>")
    readable, writable, exceptional = select.select(connectionSocket, [], [])

    for r_s in readable:
        if r_s != sys.stdin:
            #new connection
            if r_s == userSocket:
                newSocket, addr = r_s.accept()
                print("new connection with sd %d"%newSocket.fileno())
                connectionSocket.append(newSocket)
            else: 
                data = r_s.recv(1024).decode()
                data = data.strip('\n')

                #socket closed from the other side
                if data[0:5] == "close":
                    connectionSocket.remove(r_s)
                    r_s.close()
                    continue

                msg = data.split(" ")

                #query for me
                if msg[7] == userId:
                    print("QUERY for Me : %s"%data)
                    if (msg[1], msg[3]) in q_forme:
                        continue
                    q_forme.append((msg[1], msg[3]))
                    sending_m = data + " " + userName + " " + r_s.getsockname()[0] + " " + tcpPort
                    r_s.sendall(sending_m.encode())
            
                
                #query hit
                else:
                    if len(msg) > 9:
                        for qry in queries:
                            if qry[0] == msg[1] and qry[1] == msg[3]:
                                #query from me
                                if msg[1] == userId:
                                    print(f"Peer Info src {msg[1]} target {msg[7]} name {msg[8]} IP {msg[9]} port {msg[10]} hop {msg[5]}")
                                else:
                                    print("Forward QUERYHIT : sender %s seq %s"%(msg[1],msg[3]))
                                    qry[2].sendall(data.encode())

                                queries.remove(qry)
                    
                    #query forward
                    else:
                        sender = msg[1]
                        seq = int(msg[3])
                        hop = int(msg[5]) + 1
                        peer = msg[7]
                        check = 0
                        for qr in queries:
                            if qr[0] == sender and qr[1] == str(seq):
                                check = 1
                        if check == 1: 
                            continue
                        queries.append((sender, str(seq), r_s))
                        q_message = "sender %s seq %d hop %d peer %s"%(sender, seq, hop, peer)
                        
                        print("Forward QUERY : %s"%q_message)
                        for s in connectionSocket:
                            if s == r_s or s == sys.stdin or s == userSocket:
                                continue
                            s.sendall(q_message.encode())


        else:
            command = sys.stdin.readline()
            commandType = command.split(" ")[0]
            if commandType == "@connect":
                hostName = command.split(" ")[1]
                portN = int(command.split(" ")[2])
                print("command @connect %s %d"%(hostName, portN))
                try:
                    newS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    newS.connect((hostName, portN))
                    print("new connection with sd %d"%newS.fileno())
                    connectionSocket.append(newS)
                except:
                    print(hostName + ": unkown host\n")
                    continue

            elif commandType == "@query":
                p_id = command.split(" ")[1]
                queryM = "sender %s seq %d hop %d peer %s"%(userId, querySeq, 1, p_id)
                print("Initiate QUERY : %s"%queryM)
                queries.append((userId, str(querySeq), userSocket))
                for sock in connectionSocket:
                    if sock == sys.stdin or sock == userSocket:
                        continue
                    sock.sendall(queryM.encode())
                querySeq += 1

            else:
                #print("quit!")
                for s in connectionSocket:
                    if s == userSocket or s == sys.stdin:
                        continue
                    s.sendall("close".encode())
                    s.close()
                userSocket.close()
                running = 0


