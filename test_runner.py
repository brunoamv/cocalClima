#!/usr/bin/env python
"""
ClimaCocal TDD Test Runner
Comprehensive test automation with coverage reporting
"""
import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


class TDDTestRunner:
    """Advanced test runner for TDD workflow"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.manage_py = self.project_root / "myproject" / "manage.py"
        self.coverage_dir = self.project_root / "coverage_reports"
        
        # Ensure coverage directory exists
        self.coverage_dir.mkdir(exist_ok=True)
    
    def run_unit_tests(self, verbose=False, coverage=False):
        """Run unit tests with optional coverage"""
        print("🧪 Running Unit Tests...")
        
        cmd = [sys.executable, str(self.manage_py), "test"]
        
        # Specific unit test modules
        test_modules = [
            "tests.test_streaming_services",
            "tests.test_streaming_views", 
            "tests.test_core_views",
        ]
        
        if verbose:
            cmd.append("-v")
            cmd.append("2")
        
        if coverage:
            # Use coverage.py for code coverage
            coverage_cmd = [
                "coverage", "run", "--source=.", 
                str(self.manage_py), "test"
            ] + test_modules
            
            result = subprocess.run(coverage_cmd, cwd=self.project_root / "myproject")
            
            if result.returncode == 0:
                # Generate coverage report
                subprocess.run(["coverage", "report"], cwd=self.project_root / "myproject")
                subprocess.run([
                    "coverage", "html", 
                    "--directory", str(self.coverage_dir / "unit_tests")
                ], cwd=self.project_root / "myproject")
                print(f"📊 Coverage report generated: {self.coverage_dir / 'unit_tests'}")
        else:
            cmd.extend(test_modules)
            result = subprocess.run(cmd, cwd=self.project_root / "myproject")
        
        return result.returncode == 0
    
    def run_integration_tests(self, verbose=False):
        """Run integration tests"""
        print("🔗 Running Integration Tests...")
        
        cmd = [
            sys.executable, str(self.manage_py), "test",
            "tests.test_integration"
        ]
        
        if verbose:
            cmd.extend(["-v", "2"])
        
        result = subprocess.run(cmd, cwd=self.project_root / "myproject")
        return result.returncode == 0
    
    def run_e2e_tests(self, verbose=False):
        """Run E2E tests (Playwright preparation)"""
        print("🌐 Running E2E Tests...")
        
        cmd = [
            sys.executable, str(self.manage_py), "test",
            "tests.test_e2e_playwright"
        ]
        
        if verbose:
            cmd.extend(["-v", "2"])
        
        result = subprocess.run(cmd, cwd=self.project_root / "myproject")
        return result.returncode == 0
    
    def run_all_tests(self, verbose=False, coverage=False):
        """Run complete test suite"""
        print("🚀 Running Complete TDD Test Suite...")
        print("=" * 50)
        
        start_time = time.time()
        results = {}
        
        # Unit Tests
        results['unit'] = self.run_unit_tests(verbose, coverage)
        print()
        
        # Integration Tests  
        results['integration'] = self.run_integration_tests(verbose)
        print()
        
        # E2E Tests
        results['e2e'] = self.run_e2e_tests(verbose)
        print()
        
        # Summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("=" * 50)
        print("📋 Test Results Summary:")
        print(f"   Unit Tests: {'✅ PASS' if results['unit'] else '❌ FAIL'}")
        print(f"   Integration Tests: {'✅ PASS' if results['integration'] else '❌ FAIL'}")
        print(f"   E2E Tests: {'✅ PASS' if results['e2e'] else '❌ FAIL'}")
        print(f"   Duration: {duration:.2f} seconds")
        
        all_passed = all(results.values())
        if all_passed:
            print("🎉 All tests passed! Ready for development.")
        else:
            print("⚠️  Some tests failed. Review and fix before proceeding.")
        
        return all_passed
    
    def watch_mode(self):
        """Watch mode for continuous testing during development"""
        print("👀 Starting Watch Mode...")
        print("   Watching for file changes in myproject/")
        print("   Press Ctrl+C to stop")
        
        try:
            import watchdog
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class TestHandler(FileSystemEventHandler):
                def __init__(self, runner):
                    self.runner = runner
                    self.last_run = 0
                
                def on_modified(self, event):
                    if event.is_directory:
                        return
                    
                    # Only react to Python files
                    if not event.src_path.endswith('.py'):
                        return
                    
                    # Debounce rapid file changes
                    current_time = time.time()
                    if current_time - self.last_run < 2:
                        return
                    
                    self.last_run = current_time
                    print(f"\n📝 File changed: {event.src_path}")
                    print("🔄 Running tests...")
                    
                    # Run quick unit tests only in watch mode
                    success = self.runner.run_unit_tests(verbose=False)
                    if success:
                        print("✅ Tests passed! Continue development.")
                    else:
                        print("❌ Tests failed! Fix issues before continuing.")
            
            observer = Observer()
            observer.schedule(
                TestHandler(self), 
                str(self.project_root / "myproject"), 
                recursive=True
            )
            observer.start()
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
                print("\n🛑 Watch mode stopped.")
            
            observer.join()
            
        except ImportError:
            print("❌ Watchdog not installed. Install with: pip install watchdog")
            print("   Falling back to manual test running.")
    
    def lint_and_format(self):
        """Run linting and code formatting"""
        print("🧹 Running Code Quality Checks...")
        
        # Check if tools are available
        tools = {
            'flake8': 'pip install flake8',
            'black': 'pip install black',
            'isort': 'pip install isort'
        }
        
        for tool, install_cmd in tools.items():
            try:
                result = subprocess.run([tool, '--version'], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"⚠️  {tool} not installed. Install with: {install_cmd}")
                    continue
            except FileNotFoundError:
                print(f"⚠️  {tool} not found. Install with: {install_cmd}")
                continue
            
            # Run the tool
            if tool == 'flake8':
                print(f"   Running {tool}...")
                subprocess.run([
                    'flake8', 'myproject/', 
                    '--max-line-length=88',
                    '--extend-ignore=E203,W503'
                ], cwd=self.project_root)
            
            elif tool == 'black':
                print(f"   Running {tool}...")
                subprocess.run([
                    'black', 'myproject/', '--check'
                ], cwd=self.project_root)
            
            elif tool == 'isort':
                print(f"   Running {tool}...")
                subprocess.run([
                    'isort', 'myproject/', '--check-only'
                ], cwd=self.project_root)
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("📊 Generating Test Report...")
        
        # Run tests with coverage
        success = self.run_all_tests(verbose=True, coverage=True)
        
        # Generate summary report
        report_file = self.coverage_dir / "test_summary.md"
        
        with open(report_file, 'w') as f:
            f.write("# ClimaCocal Test Report\n\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Test Categories\n\n")
            f.write("- **Unit Tests**: Individual component testing\n")
            f.write("- **Integration Tests**: Component interaction testing\n") 
            f.write("- **E2E Tests**: End-to-end user journey testing\n\n")
            f.write("## Coverage Reports\n\n")
            f.write("- HTML Coverage: `coverage_reports/unit_tests/index.html`\n")
            f.write("- Console Coverage: Run `coverage report`\n\n")
            f.write("## TDD Workflow\n\n")
            f.write("1. **Red**: Write failing test\n")
            f.write("2. **Green**: Write minimal code to pass\n")
            f.write("3. **Refactor**: Improve code while keeping tests green\n")
        
        print(f"📄 Test report generated: {report_file}")
        return success


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="ClimaCocal TDD Test Runner")
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--e2e', action='store_true', help='Run E2E tests only')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--watch', action='store_true', help='Watch mode for continuous testing')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--lint', action='store_true', help='Run linting and code quality checks')
    parser.add_argument('--report', action='store_true', help='Generate comprehensive test report')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    runner = TDDTestRunner()
    
    if args.watch:
        runner.watch_mode()
    elif args.unit:
        runner.run_unit_tests(args.verbose, args.coverage)
    elif args.integration:
        runner.run_integration_tests(args.verbose)
    elif args.e2e:
        runner.run_e2e_tests(args.verbose)
    elif args.lint:
        runner.lint_and_format()
    elif args.report:
        runner.generate_test_report()
    elif args.all:
        runner.run_all_tests(args.verbose, args.coverage)
    else:
        # Default: run all tests
        runner.run_all_tests(args.verbose, args.coverage)


if __name__ == "__main__":
    main()