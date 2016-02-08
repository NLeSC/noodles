#include "test.hh"
#include <iostream>
#include <sstream>

int __assert_fail(std::string const &expr, std::string const &file, int lineno)
{
    std::ostringstream oss;
    oss << file << ":" << lineno << ": Assertion failed: " << expr;
    throw oss.str();
    return 0;
}

std::unique_ptr<std::map<std::string, Test const *>> Test::_instances;

Test::imap &Test::instances() {
	if (not _instances)
		_instances = std::unique_ptr<imap>(new imap);

	return *_instances;
}

bool run_test(Test const *unit) {
	bool pass;
	try {
		pass = (*unit)();
	}
	catch (char const *e) {
		pass = false;
		std::cerr << "failure: " << e << std::endl;
	}
	catch (std::string const &e) {
		pass = false;
		std::cerr << "failure: " << e << std::endl;
	}

	if (pass) {
		std::cerr << "\033[62G[\033[32mpassed\033[m]\n";
	}
	else {
		std::cerr << "\033[62G[\033[31mfailed\033[m]\n";
	}

	return pass;
}

void Test::all(bool should_break) {
	for (auto &kv : instances()) {
		std::cerr << "[test \033[34;1m" << kv.first << "\033[m]\n";
		if (not run_test(kv.second) and should_break)
			break;
	}
}

Test::Test(std::string const &name_, std::function<bool ()> const &code_):
	_name(name_), code(code_) {
	instances()[_name] = this;
}

Test::~Test() {
	instances().erase(_name);
}
