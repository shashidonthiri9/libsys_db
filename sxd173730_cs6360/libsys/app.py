from flask import Flask, render_template, request, jsonify, json, Response
from flask_api import status
from flaskext.mysql import MySQL
import datetime
app = Flask(__name__,static_url_path='/static')
mysql = MySQL()

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Bca@4321'
app.config['MYSQL_DATABASE_DB'] = 'libsys'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)


# @app.route('/checkIn')
# def checkInFunction():
#     return "Yes, puppies!"
# @app.route('/checkOut')
# def checkOutFunction():
#     return "Yes, puppies!"
# @app.route('/manageBorrowers')
# def manageBorrowersFunction():
#     return "Yes, puppies!"
# @app.route('/manageFines')
# def manageFinesFunction():
#     return "Yes, puppies!"

@app.route("/")
def main():
    return render_template('index.html')

@app.route('/fines')
def fines():
    return render_template('fines.html')

@app.route("/searchPage")
def searchPage():
    return render_template('search.html')

@app.route("/checkInSearchPage")
def checkInSearchPage():
    return render_template('checkInPage.html')

@app.route('/manageBorrowers')
def manageBorrowersFunction():
    return render_template('borrowerManagement.html')


@app.route('/submit', methods=['POST'])
def submit():
    _email = request.form['email']
    _fname = request.form['fname']
    _lname = request.form['lname']
    _ssn = request.form['ssn']
    _address = request.form['address']
    _phone = request.form['phone']
    _city = request.form['city']
    _state = request.form['state']
    addNewBorrower(_email, _fname, _lname, _ssn, _address, _phone, _city, _state)
    # return json.dumps({'status': 'OK'});


def addNewBorrower(email, fname, lname, ssn, address, phone, city, state):
    conn,cursor = connectToDB()
    addBorrowerQuery = """INSERT INTO libsys.borrower( SSN, FNAME, LASTNAME, EMAIL, ADDRESS, CITY, STATE, PHONE) VALUES (%s,%s,%s,%s,%s,%s,%s,%s ); """
    cursor.execute(addBorrowerQuery, (ssn, fname, lname, email, address, city, state, phone))
    conn.commit()
    conn.close()


@app.route("/search", methods = ['GET'])
def search():
    keyWord = request.args.getlist('keyword')[0]
    # results = []
    isbnResult = searchDB('NORMAL_SEARCH','ISBN', (keyWord, keyWord)) #look at the number of items in parameters tuple from the query below
    keyWord = "%" + keyWord + "%"
    authorSearchResult = searchDB('NORMAL_SEARCH','AUTHOR',(keyWord,keyWord))
    titleSearchResult = searchDB('NORMAL_SEARCH','TITLE',(keyWord,keyWord))
    # results.append(isbnResult)
    return jsonify(isbnResult + authorSearchResult + titleSearchResult)

def searchDB(searchType, queryType, parametersTuple):
    conn, cursor = connectToDB()
    if(queryType == 'ISBN'):
        query = "select a.isbn,a.title,a.NAME,( case when book_loans.dayin is not null then 'True' else 'False' end) as availability from (select book.ISBN, book.TITLE,authors.AUTHORID,authors.NAME from book, book_authors,authors where book.ISBN = book_authors.isbn and book_authors.AUTHOR_ID = authors.AUTHORID ) as a,(select * from book_loans where loanid in (select max(loanid) from book_loans group by isbn) ) as book_loans where a.ISBN = book_loans.isbn and a.ISBN = %s union select a.isbn,a.title,a.NAME,'True' from (select book.ISBN, book.TITLE,authors.AUTHORID,authors.NAME,NULL from book, book_authors,authors where book.ISBN = book_authors.isbn and book_authors.AUTHOR_ID = authors.AUTHORID ) as a where  a.ISBN = %s  and  a.isbn  not in ( select isbn from book_loans);"
    if(queryType == 'AUTHOR'):
        query = "select a.isbn,a.title,a.NAME,( case when book_loans.dayin is not null then 'True' else 'False' end) as availability from (select book.ISBN, book.TITLE,authors.AUTHORID,authors.NAME from book, book_authors,authors where book.ISBN = book_authors.isbn and book_authors.AUTHOR_ID = authors.AUTHORID )  as a,(select * from book_loans where loanid in (select max(loanid) from book_loans group by isbn) ) as book_loans where a.ISBN = book_loans.isbn and a.name like %s union select a.isbn,a.title,a.NAME,'True' from (select book.ISBN, book.TITLE,authors.AUTHORID,authors.NAME,NULL from book, book_authors,authors where book.ISBN = book_authors.isbn and book_authors.AUTHOR_ID = authors.AUTHORID ) as a where  a.name like %s and  a.isbn  not in ( select isbn from book_loans);"
    if(queryType == "TITLE"):
        query = "select a.isbn,a.title,a.NAME,( case when book_loans.dayin is not null then 'True' else 'False' end) as availability from (select book.ISBN, book.TITLE,authors.AUTHORID,authors.NAME from book, book_authors,authors where book.ISBN = book_authors.isbn and book_authors.AUTHOR_ID = authors.AUTHORID ) as a,(select * from book_loans where loanid in (select max(loanid) from book_loans group by isbn) ) as book_loans where a.ISBN = book_loans.isbn and a.title like %s union select a.isbn,a.title,a.NAME,'True' from (select book.ISBN, book.TITLE,authors.AUTHORID,authors.NAME,NULL from book, book_authors,authors where book.ISBN = book_authors.isbn and book_authors.AUTHOR_ID = authors.AUTHORID ) as a where  a.title like %s and  a.isbn  not in ( select isbn from book_loans);"
    if(queryType == "CARDID_BOOK_LOANS"):
        query = "select isbn, cardid from book_loans where cardid = %s and dayin is null"    #this returns only books that are yet to be returned
    if(queryType == "BOOKID_BOOK_LOANS"):
        query = "select isbn, cardid from book_loans where isbn = %s and dayin is null"
    if(queryType == "BORROWER_NAME_BOOK_LOANS"):
        query = "select isbn, borrower.cardid from book_loans inner join borrower on book_loans.cardid = borrower.cardid where (borrower.fname like %s or borrower.lastname like %s) and book_loans.dayin is null;"
    cursor.execute(query,parametersTuple)
    data = cursor.fetchall()

    resultDict = {}
    results = []

    if(searchType == "NORMAL_SEARCH"):
        if(len(data)>0):
            for row in data:
                resultDict['ISBN'] = row[0]
                resultDict['author'] = row[1]
                resultDict['title'] = row[2]
                resultDict['availability'] = row[3]
                results.append(resultDict)
                resultDict = {}
    if(searchType == "CHECK_IN_SEARCH"):
        if(len(data)>0):
            for row in data:
                resultDict['ISBN'] = row[0]
                resultDict['CardId'] = row[1]
                results.append(resultDict)
                resultDict = {}
    conn.close()
    return results

@app.route("/checkOutBooks", methods = ['POST'])
def checkOutBooks():
    postData = request.get_json(force=True)
    cardId = int(postData["cardId"])
    bookIds = postData["bookIds"]
    bookIds = list(set(bookIds))

    conn, cursor = connectToDB()
    try:
        cardExists = cardExistence(cardId, cursor)
        if cardExists:
            loansCountForCardIdQuery = "select count(*) from book_loans where CARDID=%s and dayin IS NULL;"
            cursor.execute(loansCountForCardIdQuery, (cardId))
            loansCountForCardId = cursor.fetchall()[0][0]
            if len(bookIds)<=(3-loansCountForCardId):
                insertIntoLoans = """INSERT INTO libsys.book_loans ( isbn, cardid, dateout, duedate) VALUES (  %s, %s, %s, %s );"""
                flag = 1
                for bookId in bookIds:
                    bookCheckedOutQuery = """select * from libsys.book_loans where isbn = %s and dayin is null;"""
                    cursor.execute(bookCheckedOutQuery, (bookId))
                    checkOut = cursor.fetchall()
                    if(len(checkOut)==0):
                        today = datetime.datetime.today()
                        dueDate = today + datetime.timedelta(days=14)
                        cursor.execute(insertIntoLoans, (bookId,cardId, today,dueDate.strftime('%Y-%m-%d') ))
                    else:
                        flag = 0
                if(flag == 1):
                    conn.commit()
            else:
                raise BaseException('Loan limit reached for user')
    except Exception as err:
        print(err.args)
        return "Loan limit reached for user"
    finally:
        conn.close()

    return "Successfully checked out"


def cardExistence(cardId, cursor):
    cardIdQuery = "select exists(select * from borrower where CARDID=%s);"
    cursor.execute(cardIdQuery, (cardId))
    cardExists = cursor.fetchall()[0][0]  # either 0 or 1
    return cardExists


def connectToDB():
    conn = mysql.connect()
    cursor = conn.cursor()
    return conn, cursor

@app.route("/checkInSearch", methods=["GET"])
def checkInSearch():
    keyWord = request.args.getlist('keyword')[0]
    bookISBNCheckInSearchResults = searchDB('CHECK_IN_SEARCH','BOOKID_BOOK_LOANS',(keyWord))
    cardIdCheckInSearchResults = searchDB('CHECK_IN_SEARCH', 'CARDID_BOOK_LOANS',(keyWord))
    keyWord = "%" + keyWord + "%"
    borrowerNameCheckInSearchResults = searchDB('CHECK_IN_SEARCH', 'BORROWER_NAME_BOOK_LOANS',(keyWord, keyWord))
    return jsonify(bookISBNCheckInSearchResults + cardIdCheckInSearchResults + borrowerNameCheckInSearchResults)


@app.route("/checkInBooks", methods=["POST"])
def checkInBooks():
    # cardId = request.form['cardId']
    # bookIds = request.form['bookIds']

    postData = request.get_json(force=True)
    cardId = int(postData["cardId"])
    bookIds = postData["bookIds"]

    conn,cursor = connectToDB()
    cardExists = cardExistence(cardId, cursor)
    if cardExists:
        validBookIds = []
        for bookId in bookIds:
            bookLoansQueryForBookId = """select isbn, cardid from book_loans where isbn = %s and dayin IS NULL"""
            cursor.execute(bookLoansQueryForBookId,(bookId))
            bookDetailsSet = cursor.fetchall()
            if(len(bookDetailsSet)>0):
                bookDetails = bookDetailsSet[0]
                cardIdFromQuery = bookDetails[1]
                if(cardId==cardIdFromQuery):
                    validBookIds.append(bookId)
        if(len(validBookIds)!=len(bookIds)):
            print('Some books were not issued to this borrower or book(s) have already been checked in')
            conn.close()
            return status.HTTP_401_UNAUTHORIZED
        else:
            for bookId in validBookIds:
                checkInBookQuery = """update book_loans set dayin = current_date() where isbn = %s and dayin IS NULL"""
                cursor.execute(checkInBookQuery,bookId)
            conn.commit()
            conn.close()
            return status.HTTP_200_OK

@app.route("/calculate_fines", methods=['GET'])
def calculate_fines():
    now = datetime.datetime.now()
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        calculatefinesQuery = "(SELECT * FROM book_loans);"
        cursor.execute(calculatefinesQuery)
        booksInbook_loans = cursor.fetchall()
        for i in range(0, len(booksInbook_loans)):
            if (booksInbook_loans[i][5] != None):

                if booksInbook_loans[i][5] > booksInbook_loans[i][4]:
                    diff = (booksInbook_loans[i][5] - booksInbook_loans[i][4]).days
                    d = diff * .25
                    insert_finesQuery = "insert into fines(select book_loans.loanid, %s, %s from book_loans " \
                                        "where %s not in (select loanid from fines) and book_loans.loanid = %s );"

                    cursor.execute(insert_finesQuery, (d, 0, booksInbook_loans[i][0], booksInbook_loans[i][0]))

                    conn.commit()

            else:
                diff = (now.date() - booksInbook_loans[i][4])
                diff = diff.days
                if (diff > 0):
                    d = diff * .25
                    insert_finesQuery = "insert into fines(select book_loans.loanid, %s, %s from book_loans " \
                                        "where %s not in (select loanid from fines) and book_loans.loanid = %s );"
                    cursor.execute(insert_finesQuery, (d, 0, booksInbook_loans[i][0], booksInbook_loans[i][0]))
                    conn.commit()
                else:

                    d = 0
                    insert_finesQuery = "insert into fines(select book_loans.loanid, %s, %s from book_loans " \
                                        "where %s not in (select loanid from fines) and book_loans.loanid = %s );"
                    cursor.execute(insert_finesQuery, (d, 0, booksInbook_loans[i][0], booksInbook_loans[i][0]))
                    conn.commit()

        displayresults = just_todisplay()
        return jsonify(displayresults)
    finally:
        conn.close()






def just_todisplay():
    conn1 = mysql.connect()
    cursor1 = conn1.cursor()
    display_fines = "select borrower.cardid, sum(fine_amt) as fineforThisCardID from fines,borrower," \
                    "book_loans where fines.loanid = book_loans.loanid and " \
                    "borrower.cardid = book_loans.cardid " \
                    "and fines.paid =0  group by(borrower.cardid);"
    cursor1.execute(display_fines)
    data = cursor1.fetchall()
    resultDict = {}
    results = []
    if (len(data) > 0):
        for row in data:
            resultDict['cardid'] = row[0]
            resultDict['fineforThisCardID'] = float(row[1])
            results.append(resultDict)
            resultDict = {}
    conn1.close()
    return results




@app.route("/display_paidfines", methods=['GET'])
def display_paidfines():
    try:
        conn1 = mysql.connect()
        cursor1 = conn1.cursor()
        display_paidfines = "select borrower.cardid, sum(fine_amt) as fineforThisCardID from fines,borrower," \
                        "book_loans where fines.loanid = book_loans.loanid and " \
                        "borrower.cardid = book_loans.cardid and book_loans.dayin IS NOT NULL " \
                        "and fines.paid =1  group by(borrower.cardid);"
        cursor1.execute(display_paidfines)
        data = cursor1.fetchall()
        resultDict = {}
        results = []
        if (len(data) > 0):
            for row in data:
                resultDict['cardid'] = row[0]
                resultDict['fineforThisCardID'] = float(row[1])
                results.append(resultDict)
                resultDict = {}
        return jsonify(results)
    finally:
        conn1.close()




@app.route("/displayfines", methods=['GET'])
def displayfines():
    conn1 = mysql.connect()
    cursor1 = conn1.cursor()
    loanid = request.args.get("loan_ID")
    print(loanid)
    display_fines = "select fines.loanid, fines.fine_amt from book_loans, fines where " \
                    "book_loans.loanid = fines.loanid " \
                    "and book_loans.loanid= %s and dayin is not NULL and fines.paid = '0';"
    cursor1.execute(display_fines, (loanid))
    data = cursor1.fetchall()
    resultDict = {}
    results = []
    if (len(data) > 0):
        for row in data:
            resultDict['loanid'] = row[0]
            resultDict['fineamount'] = float(row[1])
            results.append(resultDict)
            resultDict = {}
    print(results)
    conn1.close()
    return jsonify(results)


@app.route("/payfines", methods=['POST'])
def payfines():
    conn1 = mysql.connect()
    cursor1 = conn1.cursor()
    postData = request.get_json(force=True)
    loanid = (postData["loan_ID"])
    print(loanid)
    payfines = "update fines inner join  book_loans on fines.loanid = book_loans.loanid  set paid = 1 " \
               "where fines.loanid in (select loanid from book_loans where loanid = %s  and dayin is not null);"
    cursor1.execute(payfines, (loanid))
    data = cursor1.fetchall()
    resultDict = {}
    results = []
    conn1.commit()
    conn1.close()
    return jsonify(results)






if __name__ == '__main__':
    # app.debug = True
    app.run(host='0.0.0.0', port=5000,threaded=True)